import React, { useState, useEffect, useMemo } from 'react';
import { db } from '../firebase';
import { collection, onSnapshot } from 'firebase/firestore';
import BookCard from './BookCard';
import AgentFAB from './AgentFAB';
import { Search, Filter } from 'lucide-react';

const LibraryDashboard = ({ userId }) => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');

  useEffect(() => {
    try {
      const inventoryRef = collection(db, 'library_inventory');
      const unsubscribeInventory = onSnapshot(inventoryRef, (snapshot) => {
        const booksData = snapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        setBooks(booksData);
        setLoading(false);
      }, (error) => {
        console.error("Firebase inventory error:", error);
        setLoading(false); 
      });

      return () => {
        unsubscribeInventory();
      };
    } catch (e) {
      console.error("Firebase init error:", e);
      setLoading(false);
    }
  }, []);

  const uniqueGenres = useMemo(() => {
    const genres = books.map(b => b.genre).filter(Boolean);
    return [...new Set(genres)].sort();
  }, [books]);

  const filteredBooks = useMemo(() => {
    return books.filter(book => {
      const matchesSearch = 
        (book.title?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
        (book.author?.toLowerCase() || '').includes(searchQuery.toLowerCase());
      
      const matchesGenre = selectedGenre ? book.genre === selectedGenre : true;
      
      return matchesSearch && matchesGenre;
    });
  }, [books, searchQuery, selectedGenre]);

  return (
    <>
      <header className="mb-12">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 tracking-tight">
          Sentinel Library Intelligence
        </h1>
        <p className="text-slate-400 mt-2 text-lg">Real-time Logistics & Academic Resource Mapping</p>
      </header>

      <div className="mb-8 flex flex-col sm:flex-row gap-4 max-w-3xl">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-slate-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-3 border border-slate-700 rounded-xl leading-5 bg-slate-800/50 text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all backdrop-blur-sm sm:text-sm"
            placeholder="Search by title or author..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="relative w-full sm:w-64">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Filter className="h-5 w-5 text-slate-400" />
          </div>
          <select
            className="block w-full pl-10 pr-10 py-3 border border-slate-700 rounded-xl leading-5 bg-slate-800/50 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all backdrop-blur-sm sm:text-sm appearance-none cursor-pointer"
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
          >
            <option value="">All Genres</option>
            {uniqueGenres.map(genre => (
              <option key={genre} value={genre}>{genre}</option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
            <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
              <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
            </svg>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-400"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredBooks.map(book => (
            <BookCard key={book.id} book={book} userId={userId} />
          ))}
          {filteredBooks.length === 0 && !loading && (
             <div className="col-span-full text-center text-slate-500 py-12 border border-slate-800 rounded-xl bg-slate-900/50 backdrop-blur-md">
                {books.length === 0 ? "No books found. Please check Firebase connection or run the backend seeder script." : "No books match your search or filter criteria."}
             </div>
          )}
        </div>
      )}

      <AgentFAB userId={userId} books={books} />
    </>
  );
};

export default LibraryDashboard;
