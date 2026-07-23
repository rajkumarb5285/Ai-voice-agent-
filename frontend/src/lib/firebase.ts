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

// Realtime Auth Storage Helpers
export function saveUserAuthDetailsToRealtimeDB(user: FirebaseUser, extraData?: Record<string, any>) {
  if (!database || !user) return;
  const userRef = ref(database, `users/${user.uid}`);
  set(userRef, {
    uid: user.uid,
    email: user.email || "",
    displayName: user.displayName || extraData?.displayName || user.email?.split("@")[0] || "User",
    photoURL: user.photoURL || "",
    emailVerified: user.emailVerified || false,
    lastLoginAt: Date.now(),
    status: "online",
    ...extraData,
  });
}

export function subscribeUserAuthRealtimeDB(uid: string, callback: (userData: any) => void) {
  if (!database || !uid) return () => {};
  const userRef = ref(database, `users/${uid}`);
  onValue(userRef, (snapshot) => {
    callback(snapshot.val());
  });
  return () => off(userRef);
}

// Auth Helpers
export async function signUpWithEmail(email: string, pass: string, full_name?: string, username?: string) {
  const userCred = await createUserWithEmailAndPassword(auth, email, pass);
  if (userCred.user) {
    saveUserAuthDetailsToRealtimeDB(userCred.user, { displayName: full_name || username || email.split("@")[0], username });
  }
  return userCred;
}

export async function signInWithEmail(email: string, pass: string) {
  const userCred = await signInWithEmailAndPassword(auth, email, pass);
  if (userCred.user) {
    saveUserAuthDetailsToRealtimeDB(userCred.user);
  }
  return userCred;
}

export async function signInWithGoogle() {
  const userCred = await signInWithPopup(auth, googleProvider);
  if (userCred.user) {
    saveUserAuthDetailsToRealtimeDB(userCred.user);
  }
  return userCred;
}

export async function signOutFirebase() {
  if (auth.currentUser && database) {
    const userRef = ref(database, `users/${auth.currentUser.uid}/status`);
    set(userRef, "offline");
  }
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

