import React, { useState, useEffect } from 'react';
import { db } from './firebase';
import { onSnapshot, doc } from 'firebase/firestore';
import Toast from './components/Toast';
import LibraryDashboard from './components/LibraryDashboard';

function App() {
  const [notifications, setNotifications] = useState([]);
  const [userId] = useState("test-user-123"); 

  useEffect(() => {
    try {
      const userRef = doc(db, 'user_states', userId);
      const unsubscribeUser = onSnapshot(userRef, (docSnap) => {
        if (docSnap.exists()) {
          const userData = docSnap.data();
          if (userData.notifications) {
            setNotifications(userData.notifications);
          }
        }
      }, (error) => {
        console.error("Firebase user states error:", error);
      });

      // Trigger the backend logistics engine to check for overdue rentals
      fetch(`http://localhost:8001/logistics/check_rentals/${userId}`, { method: 'POST' })
        .catch(e => console.error("Error triggering logistics engine:", e));

      return () => {
        unsubscribeUser();
      };
    } catch (e) {
      console.error("Firebase init error:", e);
    }
  }, [userId]);

  return (
    <div className="min-h-screen p-8 relative">
      
      <LibraryDashboard userId={userId} />

      {/* Notifications Toasts */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {notifications.slice(-3).map((notif, idx) => (
          <Toast key={idx} message={notif.msg} type={notif.type} />
        ))}
      </div>
    </div>
  );
}

export default App;
