/**
 * HousingPage — Main housing module page
 * Layout: Chat Panel (left) | Recommendations (center) | All Listings (right)
 */
import { useState } from 'react';
import { HousingProvider, useHousing } from '../store/housingStore';
import ChatPanel from '../components/ChatPanel';
import RecommendationPanel from '../components/RecommendationPanel';
import HousingCard from '../components/HousingCard';
import ScheduleModal from '../components/ScheduleModal';
import NegotiationPanel from '../components/NegotiationPanel';
import { Home, LayoutGrid, MessageSquareDashed, Calendar, TrendingUp, Search, Filter, X } from 'lucide-react';

function HousingContent() {
  const { listings, schedules, isLoading, searchListings } = useHousing();
  const [scheduleTarget, setScheduleTarget] = useState(null);
  const [negotiateTarget, setNegotiateTarget] = useState(null);
  const [activeTab, setActiveTab] = useState('recommendations'); // 'recommendations' | 'all'
  const [searchFilters, setSearchFilters] = useState({});
  const [filterOpen, setFilterOpen] = useState(false);
  const [visitsOpen, setVisitsOpen] = useState(false);
  const [selectedVisit, setSelectedVisit] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    await searchListings(searchFilters);
  };

  return (
    <div className="min-h-screen bg-[#0a0a14] text-white">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-violet-900/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-900/15 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-30 bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/50">
        <div className="max-w-screen-2xl mx-auto px-4 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-violet-600 flex items-center justify-center shadow-lg shadow-violet-500/30">
              <Home className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-white">Housing Hub</p>
              <p className="text-[10px] text-slate-500 hidden sm:block">AI-Powered Property Search</p>
            </div>
          </div>

          {/* Stats */}
          <div className="hidden md:flex items-center gap-4 ml-6">
            <Stat icon={LayoutGrid} label="Listings" value={listings.length} />
            <Stat icon={TrendingUp} label="Ranked" value={listings.length > 0 ? listings.length : 0} />
            <Stat icon={Calendar} label="Visits" value={schedules.length} />
          </div>

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={() => setVisitsOpen(true)}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border bg-slate-800/60 border-slate-700/50 text-slate-400 hover:text-white hover:border-slate-600 transition-all duration-200 xl:hidden"
            >
              <Calendar className="w-3.5 h-3.5" />
              Your Visits
            </button>
            <button
              onClick={() => setFilterOpen(!filterOpen)}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-all duration-200 ${
                filterOpen
                  ? 'bg-violet-600/20 border-violet-500/50 text-violet-300'
                  : 'bg-slate-800/60 border-slate-700/50 text-slate-400 hover:text-white hover:border-slate-600'
              }`}
            >
              <Filter className="w-3.5 h-3.5" />
              Filters
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        {filterOpen && (
          <form onSubmit={handleSearch} className="border-t border-slate-700/50 bg-slate-900/60 backdrop-blur px-4 py-3">
            <div className="max-w-screen-2xl mx-auto flex flex-wrap gap-3 items-end">
              <div className="flex flex-col gap-1">
                <label className="text-[10px] text-slate-500">Location</label>
                <input
                  type="text"
                  placeholder="e.g. Whitefield"
                  onChange={(e) => setSearchFilters(f => ({ ...f, location: e.target.value || undefined }))}
                  className="bg-slate-800 border border-slate-600/50 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-violet-500/60 w-36"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] text-slate-500">Max Budget (₹)</label>
                <input
                  type="number"
                  placeholder="e.g. 15000"
                  onChange={(e) => setSearchFilters(f => ({ ...f, budget: e.target.value ? parseInt(e.target.value) : undefined }))}
                  className="bg-slate-800 border border-slate-600/50 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-violet-500/60 w-32"
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] text-slate-500">Type</label>
                <select
                  onChange={(e) => setSearchFilters(f => ({ ...f, property_type: e.target.value || undefined }))}
                  className="bg-slate-800 border border-slate-600/50 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-violet-500/60 w-28"
                >
                  <option value="">Any</option>
                  <option value="PG">PG</option>
                  <option value="flat">Flat</option>
                  <option value="room">Room</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-[10px] text-slate-500">Gender</label>
                <select
                  onChange={(e) => setSearchFilters(f => ({ ...f, gender: e.target.value || undefined }))}
                  className="bg-slate-800 border border-slate-600/50 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-violet-500/60 w-28"
                >
                  <option value="">Any</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="flex items-center gap-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium px-4 py-2 rounded-lg transition-all duration-200"
              >
                <Search className="w-3.5 h-3.5" />
                Search
              </button>
            </div>
          </form>
        )}
      </header>

      {/* Main Layout */}
      <div className="max-w-screen-2xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-[340px_1fr] xl:grid-cols-[360px_1fr_1fr] gap-5 h-[calc(100vh-64px)]">
        {/* Chat Panel */}
        <div className="lg:col-span-1 h-[calc(100vh-96px)] sticky top-[72px]">
          <ChatPanel />
        </div>

        {/* Center / Results Panel */}
        <div className="space-y-4 overflow-y-auto pb-8 xl:col-span-1">
          {/* Tabs */}
          <div className="flex gap-1 bg-slate-800/50 p-1 rounded-xl border border-slate-700/40 sticky top-0 z-10">
            {[
              { id: 'recommendations', label: 'Recommendations', icon: TrendingUp },
              { id: 'all', label: `All Listings (${listings.length})`, icon: LayoutGrid },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all duration-200 ${
                  activeTab === id
                    ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>

          {activeTab === 'recommendations' ? (
            <RecommendationPanel
              onSchedule={setScheduleTarget}
              onNegotiate={setNegotiateTarget}
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-1 gap-4">
              {listings.length === 0 ? (
                <div className="col-span-full flex flex-col items-center justify-center py-16 text-center space-y-3">
                  <Home className="w-10 h-10 text-slate-600" />
                  <p className="text-slate-400 text-sm">No listings found.</p>
                  <p className="text-slate-500 text-xs">Use the chat or filters to search.</p>
                </div>
              ) : (
                listings.map((listing) => (
                  <HousingCard
                    key={listing.id}
                    listing={listing}
                    onSchedule={setScheduleTarget}
                    onNegotiate={setNegotiateTarget}
                  />
                ))
              )}
            </div>
          )}
        </div>

        {/* Schedules Panel (XL+) */}
        <div className="hidden xl:block overflow-y-auto pb-8">
          <SchedulesPanel 
            schedules={schedules} 
            onVisitClick={(s) => {
              const found = listings.find(l => l.property_id === s.property_id || l.id === s.property_id);
              if (found) setSelectedVisit(found);
            }} 
          />
        </div>
      </div>

      {/* Modals */}
      {visitsOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setVisitsOpen(false)} />
          <div className="relative bg-slate-900 border border-slate-700/50 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-5 max-h-[80vh] overflow-y-auto">
            <button onClick={() => setVisitsOpen(false)} className="absolute top-4 right-4 w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center">
              <X className="w-4 h-4 text-slate-400" />
            </button>
            <SchedulesPanel 
              schedules={schedules} 
              onVisitClick={(s) => {
                const found = listings.find(l => l.property_id === s.property_id || l.id === s.property_id);
                if (found) setSelectedVisit(found);
              }} 
            />
          </div>
        </div>
      )}
      
      {selectedVisit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedVisit(null)} />
          <div className="relative w-full max-w-md z-10">
            <button onClick={() => setSelectedVisit(null)} className="absolute -top-10 right-0 w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center">
              <X className="w-4 h-4 text-slate-400" />
            </button>
            <HousingCard listing={selectedVisit} />
          </div>
        </div>
      )}

      {scheduleTarget && (
        <ScheduleModal
          listing={scheduleTarget}
          onClose={() => setScheduleTarget(null)}
        />
      )}
      {negotiateTarget && (
        <NegotiationPanel
          listing={negotiateTarget}
          onClose={() => setNegotiateTarget(null)}
        />
      )}
    </div>
  );
}

function SchedulesPanel({ schedules, onVisitClick }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 pb-1">
        <Calendar className="w-4 h-4 text-violet-400" />
        <span className="text-sm font-semibold text-white">Your Visits</span>
        {schedules.length > 0 && (
          <span className="ml-auto text-xs bg-violet-600/20 text-violet-300 px-2 py-0.5 rounded-full">{schedules.length}</span>
        )}
      </div>
      {schedules.length === 0 ? (
        <div className="text-center py-12 space-y-2">
          <Calendar className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-slate-400 text-sm">No visits scheduled</p>
          <p className="text-slate-500 text-xs">Schedule a visit from any listing card</p>
        </div>
      ) : (
        schedules.map((s, i) => (
          <div 
            key={s.visit_id || i} 
            onClick={() => onVisitClick && onVisitClick(s)}
            className="bg-slate-800/50 border border-slate-700/40 rounded-xl p-4 space-y-2 cursor-pointer hover:border-violet-500/50 transition-all duration-200"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-white">Visit #{s.visit_id}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full border capitalize ${
                s.status === 'scheduled' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-slate-700/50 text-slate-400 border-slate-600/30'
              }`}>
                {s.status}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono">{s.property_id}</p>
            <p className="text-xs text-slate-300">{new Date(s.slot).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}</p>
          </div>
        ))
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      <Icon className="w-3.5 h-3.5 text-slate-500" />
      <span className="text-slate-500">{label}:</span>
      <span className="text-white font-semibold">{value}</span>
    </div>
  );
}

export default function HousingPage() {
  return (
    <HousingProvider>
      <HousingContent />
    </HousingProvider>
  );
}
