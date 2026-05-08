import React from 'react';
import { Star, TrendingUp } from 'lucide-react';
import { doc, setDoc, updateDoc, arrayUnion, increment } from 'firebase/firestore';
import { db } from '../firebase';

const BookCard = ({ book, userId }) => {
  const isTrending = book.popularity_score > 8;

  const handleRent = async () => {
    if (book.volume !== undefined && book.volume <= 0) {
      alert("This book is out of stock!");
      return;
    }
    try {
      const userRef = doc(db, 'user_states', userId);
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + 14);
      
      await setDoc(userRef, {
        active_rentals: arrayUnion({
          isbn: book.isbn,
          status: 'rented',
          due_date: dueDate.toISOString()
        })
      }, { merge: true });

      const inventoryRef = doc(db, 'library_inventory', book.id);
      await updateDoc(inventoryRef, {
        volume: increment(-1)
      });

      alert(`Successfully rented ${book.title}!`);
    } catch (e) {
      console.error("Error renting book:", e);
      alert("Failed to rent book. Ensure Firebase config is set.");
    }
  };

  const handleBuy = async () => {
    if (book.volume !== undefined && book.volume <= 0) {
      alert("This book is out of stock!");
      return;
    }
    try {
      const userRef = doc(db, 'user_states', userId);
      
      await setDoc(userRef, {
        owned_books: arrayUnion({
          isbn: book.isbn,
          status: 'owned',
          purchase_date: new Date().toISOString()
        })
      }, { merge: true });

      const inventoryRef = doc(db, 'library_inventory', book.id);
      await updateDoc(inventoryRef, {
        volume: increment(-1)
      });

      alert(`Successfully purchased ${book.title}!`);
    } catch (e) {
      console.error("Error purchasing book:", e);
      alert("Failed to purchase book. Ensure Firebase config is set.");
    }
  };

  const volume = book.volume !== undefined ? book.volume : 0;
  const isOutOfStock = volume <= 0;

  return (
    <div id={`book-${book.isbn}`} className="bg-slate-800/80 backdrop-blur-md rounded-2xl p-5 border border-slate-700 hover:border-emerald-500/50 transition-all duration-300 group shadow-lg flex flex-col relative overflow-hidden">
      {isTrending && (
        <div className="absolute top-0 right-0 bg-gradient-to-r from-orange-500 to-amber-500 text-white text-xs font-bold px-3 py-1 rounded-bl-xl flex items-center gap-1 shadow-md">
          <TrendingUp size={12} /> Trending
        </div>
      )}
      
      <div className="flex-1">
        <h3 className="text-xl font-bold text-white mb-1 group-hover:text-emerald-400 transition-colors pr-16">{book.title}</h3>
        <p className="text-slate-400 text-sm mb-3 font-medium">{book.author}</p>
        
        <div className="flex items-center gap-1 mb-3">
          <Star className="text-amber-400 fill-amber-400" size={16} />
          <span className="text-slate-300 text-sm font-semibold">{book.rating}</span>
          <span className="text-slate-500 text-xs ml-2">({book.genre})</span>
        </div>

        <div className="mb-4">
          {isOutOfStock ? (
            <span className="text-red-400 text-xs font-bold px-2 py-1 bg-red-500/10 rounded border border-red-500/20">Out of Stock</span>
          ) : (
            <span className="text-emerald-400 text-xs font-bold px-2 py-1 bg-emerald-500/10 rounded border border-emerald-500/20">{volume} Available</span>
          )}
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-end justify-between">
        <div>
          <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">Pricing</div>
          <div className="flex gap-4">
            <div>
              <span className="text-emerald-400 font-bold">${book.rent_price}</span>
              <span className="text-slate-500 text-xs ml-1">/rent</span>
            </div>
            <div>
              <span className="text-slate-300 font-semibold">${book.buy_price}</span>
              <span className="text-slate-500 text-xs ml-1">/buy</span>
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button 
            onClick={handleBuy}
            disabled={isOutOfStock}
            className={`px-4 py-2 rounded-lg font-semibold transition-all duration-300 ${isOutOfStock ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white active:scale-95 cursor-pointer'}`}
          >
            Buy
          </button>
          <button 
            onClick={handleRent}
            disabled={isOutOfStock}
            className={`px-4 py-2 rounded-lg font-semibold transition-all duration-300 ${isOutOfStock ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500 hover:text-white active:scale-95 cursor-pointer'}`}
          >
            Rent
          </button>
        </div>
      </div>
    </div>
  );
};

export default BookCard;
