import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAL1AyeLhQXz5P5I3QydVNAmvy8YDyddL0",
  authDomain: "library-42a1f.firebaseapp.com",
  databaseURL: "https://library-42a1f-default-rtdb.firebaseio.com",
  projectId: "library-42a1f",
  storageBucket: "library-42a1f.firebasestorage.app",
  messagingSenderId: "769465260849",
  appId: "1:769465260849:web:a0b116e8dd9ee09d7b2e10",
  measurementId: "G-KKBW0KHLMR"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);

