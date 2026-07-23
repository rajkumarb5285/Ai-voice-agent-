import { initializeApp, getApps, getApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  User as FirebaseUser,
} from "firebase/auth";
import { getDatabase, ref, set, push, onValue, off } from "firebase/database";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "AIzaSyMockKeyForDevFirebaseSetup12345",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "ai-voice-agent-app.firebaseapp.com",
  databaseURL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL || "https://ai-voice-agent-app-default-rtdb.firebaseio.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "ai-voice-agent-app",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "ai-voice-agent-app.appspot.com",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "123456789012",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:123456789012:web:abcdef1234567890",
};

// Initialize Firebase
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const database = getDatabase(app);
export const googleProvider = new GoogleAuthProvider();

// Auth Helpers
export async function signUpWithEmail(email: string, pass: string) {
  return await createUserWithEmailAndPassword(auth, email, pass);
}

export async function signInWithEmail(email: string, pass: string) {
  return await signInWithEmailAndPassword(auth, email, pass);
}

export async function signInWithGoogle() {
  return await signInWithPopup(auth, googleProvider);
}

export async function signOutFirebase() {
  return await firebaseSignOut(auth);
}

// Realtime Database Sync Helpers
export function syncRealtimeMessage(conversationId: string, messageData: { role: string; content: string; timestamp: number }) {
  if (!database) return;
  const messagesRef = ref(database, `conversations/${conversationId}/messages`);
  const newMessageRef = push(messagesRef);
  set(newMessageRef, messageData);
}

export function subscribeRealtimeMessages(conversationId: string, callback: (messages: any[]) => void) {
  if (!database) return () => {};
  const messagesRef = ref(database, `conversations/${conversationId}/messages`);
  onValue(messagesRef, (snapshot) => {
    const data = snapshot.val();
    if (data) {
      const msgList = Object.keys(data).map((key) => ({ id: key, ...data[key] }));
      callback(msgList);
    } else {
      callback([]);
    }
  });
  return () => off(messagesRef);
}
