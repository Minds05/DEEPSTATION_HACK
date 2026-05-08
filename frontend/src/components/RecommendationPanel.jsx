/**
 * RecommendationPanel Component
 * Displays ranked recommendations with scores and match reasons.
 */
import { TrendingUp, Award, AlertTriangle, ChevronRight, IndianRupee } from 'lucide-react';
import { useHousing } from '../store/housingStore';
import HousingCard from './HousingCard';

export default function RecommendationPanel({ onSchedule, onNegotiate }) {
  const { recommendations, listings, isLoading } = useHousing();

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-64 bg-slate-800/40 rounded-2xl animate-pulse border border-slate-700/30" />
        ))}
      </div>
    );
  }

  if (!recommendations.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center space-y-3">
        <div className="w-14 h-14 rounded-2xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-center">
          <TrendingUp className="w-7 h-7 text-slate-500" />
        </div>
        <p className="text-slate-400 text-sm">No recommendations yet.</p>
        <p className="text-slate-500 text-xs">Chat with the AI to get personalized listings.</p>
      </div>
    );
  }

  // Map listing data into recommendations
  const listingMap = Object.fromEntries(listings.map((l) => [l.id, l]));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 pb-1">
        <Award className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-semibold text-white">Top Matches</span>
        <span className="ml-auto text-xs text-slate-500">{recommendations.length} ranked</span>
      </div>

      {/* Recommendation Cards */}
      {recommendations.map((rec, idx) => {
        const listing = listingMap[rec.listing_id];
        if (!listing) {
          // Fallback card for listings not in current search results
          return (
            <div key={rec.listing_id} className="bg-slate-800/40 border border-slate-700/30 rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-slate-400">Listing ID: {rec.listing_id}</span>
                <ScoreBadge score={rec.score} rank={idx + 1} />
              </div>
              {rec.reasons?.length > 0 && (
                <div className="space-y-1">
                  {rec.reasons.map((r, i) => (
                    <div key={i} className="text-[10px] text-emerald-400 flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-emerald-400" />
                      {r}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        }

        return (
          <div key={rec.listing_id} className="relative">
            {/* Rank badge */}
            {idx < 3 && (
              <div className="absolute -top-2 -left-2 z-20 w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border"
                style={{
                  background: ['#fbbf24', '#94a3b8', '#f97316'][idx],
                  borderColor: ['#d97706', '#64748b', '#ea580c'][idx],
                  color: '#0f172a',
                }}>
                #{idx + 1}
              </div>
            )}
            <HousingCard
              listing={listing}
              score={rec.score}
              reasons={rec.reasons}
              onSchedule={onSchedule}
              onNegotiate={onNegotiate}
            />
            {/* Concerns */}
            {rec.concerns?.length > 0 && (
              <div className="mt-1 px-4 flex items-start gap-1.5">
                <AlertTriangle className="w-3 h-3 text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-[10px] text-amber-400/80">{rec.concerns[0]}</p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function ScoreBadge({ score, rank }) {
  const color = score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : 'text-slate-400';
  return (
    <div className="flex items-center gap-1.5">
      <span className={`text-xs font-bold ${color}`}>{score}%</span>
      <span className="text-[10px] text-slate-500">match</span>
    </div>
  );
}
