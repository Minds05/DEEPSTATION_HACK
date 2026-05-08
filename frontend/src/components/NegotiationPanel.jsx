/**
 * NegotiationPanel Component
 * Modal panel for generating and displaying rent negotiation messages.
 */
import { useState } from 'react';
import { X, MessageSquare, Loader2, Copy, CheckCheck, IndianRupee, TrendingDown } from 'lucide-react';
import { housingApi } from '../services/api';

export default function NegotiationPanel({ listing, onClose }) {
  const [targetRent, setTargetRent] = useState(Math.floor(listing.rent * 0.85));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  const savings = listing.rent - targetRent;
  const savingsPct = Math.round((savings / listing.rent) * 100);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    // Add validation for 10-20% discount
    if (savingsPct < 10 || savingsPct > 20) {
      setError("Disagree: The owner is only willing to consider a reasonable discount between 10% and 20%. Please adjust your target amount.");
      setLoading(false);
      return;
    }

    try {
      const res = await housingApi.negotiate(listing.rent, targetRent, listing.property_type);
      setResult({ ...res, message: `The owner has accepted your reasonable negotiation. Suggested message: ${res.message}` });
    } catch (err) {
      setError(err.error || 'Failed to generate message');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!result?.message) return;
    await navigator.clipboard.writeText(result.message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-900 border border-slate-700/50 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-5">
        <button onClick={onClose} className="absolute top-4 right-4 w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center transition-colors">
          <X className="w-4 h-4 text-slate-400" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-violet-600/20 border border-violet-500/30 flex items-center justify-center">
            <TrendingDown className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Negotiate Rent</h2>
            <p className="text-xs text-slate-400">{listing.title}</p>
          </div>
        </div>

        {/* Current Rent */}
        <div className="bg-slate-800/60 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-400">Listed Rent</span>
            <span className="text-sm font-bold text-white flex items-center gap-0.5">
              <IndianRupee className="w-3.5 h-3.5" />
              {listing.rent.toLocaleString('en-IN')}
            </span>
          </div>

          {/* Target Rent Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Your Target</span>
              <span className="text-sm font-bold text-emerald-400 flex items-center gap-0.5">
                <IndianRupee className="w-3.5 h-3.5" />
                {targetRent.toLocaleString('en-IN')}
              </span>
            </div>
            <input
              type="range"
              min={Math.floor(listing.rent * 0.5)}
              max={listing.rent}
              step={500}
              value={targetRent}
              onChange={(e) => setTargetRent(parseInt(e.target.value))}
              className="w-full h-1.5 appearance-none bg-slate-700 rounded-full cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-violet-500 [&::-webkit-slider-thumb]:cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>₹{Math.floor(listing.rent * 0.5).toLocaleString('en-IN')}</span>
              <span className={`font-medium ${savingsPct > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
                Save ₹{savings.toLocaleString('en-IN')} ({savingsPct}%)
              </span>
              <span>₹{listing.rent.toLocaleString('en-IN')}</span>
            </div>
          </div>
        </div>

        {/* Result */}
        {result && (
          <div className="space-y-3">
            <div className="bg-slate-800/40 border border-violet-500/20 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-300">Suggested Message</span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-white bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded-lg transition-all"
                >
                  {copied ? <CheckCheck className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <p className="text-sm text-white leading-relaxed italic">"{result.message}"</p>
              {result.strategy && (
                <div className="text-[10px] text-slate-500">
                  Strategy: <span className="text-violet-400">{result.strategy}</span>
                </div>
              )}
            </div>
            {result.key_points?.length > 0 && (
              <div className="space-y-1">
                <p className="text-[10px] text-slate-500 font-medium">Key leverage points:</p>
                {result.key_points.map((point, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span className="w-1 h-1 rounded-full bg-violet-400" />
                    {point}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {error && (
          <p className="text-xs text-red-400 bg-red-900/20 border border-red-500/20 rounded-xl px-3 py-2">{error}</p>
        )}

        {/* Actions */}
        <button
          onClick={handleGenerate}
          disabled={loading || targetRent >= listing.rent}
          className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:opacity-50 text-white font-medium py-3 rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-violet-500/25"
        >
          {loading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
          ) : (
            <><MessageSquare className="w-4 h-4" /> {result ? 'Regenerate' : 'Generate Message'}</>
          )}
        </button>
      </div>
    </div>
  );
}
