/**
 * HousingCard Component
 * Displays a single property listing with all details.
 * Supports negotiation trigger and schedule modal open.
 */
import { useState } from 'react';
import { MapPin, Wifi, UtensilsCrossed, Car, Shield, ShieldCheck, Star, IndianRupee, BedDouble, Bath, MessageSquare, Calendar, Phone, User, Map } from 'lucide-react';

const AMENITY_ICONS = {
  wifi: { icon: Wifi, label: 'WiFi' },
  food: { icon: UtensilsCrossed, label: 'Food' },
  parking: { icon: Car, label: 'Parking' },
  security: { icon: Shield, label: 'Security' },
};

const TYPE_COLORS = {
  PG: 'bg-violet-500/20 text-violet-300 border-violet-500/30',
  flat: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  apartment: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  room: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  hostel: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
};

export default function HousingCard({ listing, score, reasons = [], onSchedule, onNegotiate }) {
  const [expanded, setExpanded] = useState(false);
  const typeColor = TYPE_COLORS[listing.property_type] || TYPE_COLORS.flat;

  return (
    <div className="group relative bg-slate-800/60 backdrop-blur-sm border border-slate-700/50 rounded-2xl overflow-hidden hover:border-violet-500/50 transition-all duration-300 hover:shadow-xl hover:shadow-violet-500/10">
      {/* Score Badge */}
      {score !== undefined && (
        <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-slate-900/80 backdrop-blur px-2.5 py-1 rounded-full border border-slate-600/50">
          <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
          <span className="text-xs font-bold text-white">{score}</span>
        </div>
      )}

      {/* Verified Badge */}
      {listing.verified && (
        <div className="absolute top-3 left-3 z-10 flex items-center gap-1 bg-emerald-500/20 backdrop-blur px-2 py-1 rounded-full border border-emerald-500/30">
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          <span className="text-[10px] font-semibold text-emerald-300">Verified</span>
        </div>
      )}

      {/* Image Placeholder */}
      <div className="h-40 bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-900/30 to-blue-900/30" />
        <div className="text-5xl opacity-20">🏠</div>
        <div className={`absolute bottom-3 left-3 text-xs font-semibold px-2 py-0.5 rounded border ${typeColor}`}>
          {listing.property_type?.toUpperCase()}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Title & Rent */}
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2 group-hover:text-violet-200 transition-colors">
            {listing.title}
          </h3>
          <div className="flex items-center gap-0.5 text-emerald-400 font-bold text-sm whitespace-nowrap">
            <IndianRupee className="w-3.5 h-3.5" />
            {listing.rent?.toLocaleString('en-IN')}
            <span className="text-slate-400 font-normal text-xs">/mo</span>
          </div>
        </div>

        {/* Location */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs">
            <MapPin className="w-3.5 h-3.5 text-violet-400 flex-shrink-0" />
            <span className="line-clamp-1">{listing.area ? `${listing.area}, ` : ''}{listing.location}</span>
          </div>
          <a
            href={`https://www.openstreetmap.org/search?query=${encodeURIComponent((listing.area ? `${listing.area}, ` : '') + (listing.location || ''))}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-violet-400 hover:text-violet-300 text-[10px] font-medium transition-colors bg-violet-500/10 hover:bg-violet-500/20 px-2 py-1 rounded-lg flex-shrink-0"
          >
            <Map className="w-3 h-3" />
            Directions
          </a>
        </div>

        {/* Bedrooms / Bathrooms */}
        {(listing.bedrooms !== undefined || listing.bathrooms) && (
          <div className="flex items-center gap-3 text-xs text-slate-400">
            {listing.bedrooms !== undefined && (
              <span className="flex items-center gap-1">
                <BedDouble className="w-3.5 h-3.5 text-slate-500" />
                {listing.bedrooms === 0 ? 'Studio' : `${listing.bedrooms} Bed`}
              </span>
            )}
            {listing.bathrooms && (
              <span className="flex items-center gap-1">
                <Bath className="w-3.5 h-3.5 text-slate-500" />
                {listing.bathrooms} Bath
              </span>
            )}
          </div>
        )}

        {/* Contact & Gender */}
        {(listing.contact || listing.gender) && (
          <div className="flex items-center gap-3 text-xs text-slate-400">
            {listing.contact && (
              <span className="flex items-center gap-1 text-violet-300">
                <Phone className="w-3.5 h-3.5 text-violet-400" />
                {listing.contact}
              </span>
            )}
            {listing.gender && (
              <span className="flex items-center gap-1 capitalize">
                <User className="w-3.5 h-3.5 text-slate-500" />
                {listing.gender} Only
              </span>
            )}
          </div>
        )}

        {/* Amenities */}
        {listing.amenities?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {listing.amenities.slice(0, 4).map((amenity) => {
              const amenityData = AMENITY_ICONS[amenity.toLowerCase()];
              return (
                <span key={amenity} className="flex items-center gap-1 text-[10px] text-slate-400 bg-slate-700/50 px-2 py-0.5 rounded-full border border-slate-600/30">
                  {amenityData?.icon ? <amenityData.icon className="w-2.5 h-2.5" /> : null}
                  {amenityData?.label || amenity}
                </span>
              );
            })}
            {listing.amenities.length > 4 && (
              <span className="text-[10px] text-slate-500 px-1">+{listing.amenities.length - 4} more</span>
            )}
          </div>
        )}

        {/* Reasons (from recommendations) */}
        {reasons.length > 0 && (
          <div className="space-y-1">
            {reasons.slice(0, 2).map((reason, i) => (
              <div key={i} className="flex items-center gap-1.5 text-[10px] text-emerald-400">
                <span className="w-1 h-1 rounded-full bg-emerald-400 flex-shrink-0" />
                {reason}
              </div>
            ))}
          </div>
        )}

        {/* Rating */}
        {listing.rating && (
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
            <span className="text-amber-300 font-medium">{listing.rating}</span>
            {listing.reviews_count && <span className="text-slate-500">({listing.reviews_count} reviews)</span>}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => onSchedule?.(listing)}
            className="flex-1 flex items-center justify-center gap-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium py-2 px-3 rounded-xl transition-all duration-200 hover:shadow-lg hover:shadow-violet-500/25 active:scale-95"
          >
            <Calendar className="w-3.5 h-3.5" />
            Schedule Visit
          </button>
          <button
            onClick={() => onNegotiate?.(listing)}
            className="flex items-center justify-center gap-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs font-medium py-2 px-3 rounded-xl transition-all duration-200 border border-slate-600/50 hover:border-slate-500 active:scale-95"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Negotiate
          </button>
        </div>
      </div>
    </div>
  );
}
