/**
 * ScheduleModal Component
 * Modal for booking property visits with slot selection.
 */
import { useState } from 'react';
import { X, Calendar, Clock, CheckCircle2, Loader2, MapPin, AlertCircle } from 'lucide-react';
import { useHousing } from '../store/housingStore';

const TIME_SLOTS = [
  '09:00', '10:00', '11:00', '12:00',
  '14:00', '15:00', '16:00', '17:00', '18:00',
];

export default function ScheduleModal({ listing, onClose }) {
  const { scheduleVisit, isLoading } = useHousing();
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Minimum date: tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split('T')[0];

  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + 30);
  const maxDateStr = maxDate.toISOString().split('T')[0];

  const handleSchedule = async () => {
    if (!selectedDate || !selectedTime) return;
    setError(null);

    const slot = `${selectedDate}T${selectedTime}:00`;

    try {
      const res = await scheduleVisit(listing.id, slot, notes || null);
      if (res.status === 'conflict') {
        setError('This slot is already booked. Please choose a different time.');
      } else {
        setResult(res);
      }
    } catch (err) {
      setError(err.error || 'Scheduling failed. Please try again.');
    }
  };

  if (result) {
    return (
      <ModalWrapper onClose={onClose}>
        <div className="text-center space-y-4 py-4">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8 text-emerald-400" />
          </div>
          <div>
            <p className="text-white font-semibold text-lg">Visit Scheduled!</p>
            <p className="text-slate-400 text-sm mt-1">Your visit has been confirmed</p>
          </div>
          <div className="bg-slate-800/60 rounded-xl p-4 space-y-2 text-left">
            <InfoRow label="Property" value={listing.title} />
            <InfoRow label="Visit ID" value={result.visit_id} mono />
            <InfoRow label="Date & Time" value={new Date(result.slot).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })} />
            <InfoRow label="Status" value={result.status} badge />
            {result.notification_sent && (
              <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> WhatsApp reminder sent
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="w-full bg-violet-600 hover:bg-violet-500 text-white font-medium py-2.5 rounded-xl transition-all duration-200"
          >
            Done
          </button>
        </div>
      </ModalWrapper>
    );
  }

  return (
    <ModalWrapper onClose={onClose}>
      <div className="space-y-5">
        {/* Header */}
        <div>
          <h2 className="text-lg font-semibold text-white">Schedule a Visit</h2>
          <div className="flex items-center gap-1.5 mt-1 text-slate-400 text-xs">
            <MapPin className="w-3.5 h-3.5 text-violet-400" />
            {listing.title} · {listing.location}
          </div>
        </div>

        {/* Date Picker */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-violet-400" />
            Select Date
          </label>
          <input
            type="date"
            min={minDate}
            max={maxDateStr}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="w-full bg-slate-800/80 border border-slate-600/50 text-white text-sm px-4 py-2.5 rounded-xl focus:outline-none focus:border-violet-500/70 transition-all [color-scheme:dark]"
          />
        </div>

        {/* Time Slots */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-violet-400" />
            Select Time
          </label>
          <div className="grid grid-cols-3 gap-2">
            {TIME_SLOTS.map((time) => (
              <button
                key={time}
                onClick={() => setSelectedTime(time)}
                className={`py-2 px-3 rounded-xl text-xs font-medium border transition-all duration-200 ${
                  selectedTime === time
                    ? 'bg-violet-600 border-violet-500 text-white shadow-lg shadow-violet-500/25'
                    : 'bg-slate-800/60 border-slate-600/40 text-slate-400 hover:border-violet-500/40 hover:text-white'
                }`}
              >
                {time}
              </button>
            ))}
          </div>
        </div>

        {/* Notes */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-slate-300">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any specific questions or requirements..."
            rows={2}
            className="w-full bg-slate-800/80 border border-slate-600/50 text-white placeholder-slate-500 text-sm px-4 py-2.5 rounded-xl focus:outline-none focus:border-violet-500/70 resize-none transition-all"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-start gap-2 bg-red-900/20 border border-red-500/20 rounded-xl p-3">
            <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-300 text-xs">{error}</p>
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleSchedule}
          disabled={!selectedDate || !selectedTime || isLoading}
          className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:opacity-50 text-white font-medium py-3 rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-violet-500/25 active:scale-[0.98]"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Booking...
            </>
          ) : (
            <>
              <Calendar className="w-4 h-4" />
              Confirm Visit
            </>
          )}
        </button>
      </div>
    </ModalWrapper>
  );
}

function ModalWrapper({ children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-900 border border-slate-700/50 rounded-2xl p-6 w-full max-w-sm shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center transition-colors"
        >
          <X className="w-4 h-4 text-slate-400" />
        </button>
        {children}
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono, badge }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-slate-500">{label}</span>
      {badge ? (
        <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[10px] capitalize">
          {value}
        </span>
      ) : (
        <span className={`text-white ${mono ? 'font-mono' : ''}`}>{value}</span>
      )}
    </div>
  );
}
