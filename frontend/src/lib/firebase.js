// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from 'firebase/firestore';
import { getAuth } from 'firebase/auth';

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyD_5kACYck7xPnVYJqGDrSEqzEu2kUxRsY",
  authDomain: "ai-research-assistant-e0e00.firebaseapp.com",
  projectId: "ai-research-assistant-e0e00",
  storageBucket: "ai-research-assistant-e0e00.firebasestorage.app",
  messagingSenderId: "624546297850",
  appId: "1:624546297850:web:b564253794b4064fb95643",
  measurementId: "G-HBGTPM48LV"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// Initialize Firestore and Auth
export const db = getFirestore(app);
export const auth = getAuth(app);

export default app; 