"use client";

import { useEffect, useState } from "react";
import {
  auth,
  saveUserAuthDetailsToRealtimeDB,
  subscribeUserAuthRealtimeDB,
  syncRealtimeSessionData,
  subscribeRealtimeSessionData,
} from "@/lib/firebase";
import { onAuthStateChanged, User as FirebaseUser } from "firebase/auth";

export function useRealtimeAuth() {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [realtimeData, setRealtimeData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribeAuth = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        // Save/Sync to Realtime DB
        saveUserAuthDetailsToRealtimeDB(currentUser, { status: "online" });
        
        // Listen to Realtime DB user object
        const unsubscribeRealtime = subscribeUserAuthRealtimeDB(currentUser.uid, (data) => {
          setRealtimeData(data);
          setLoading(false);
        });
        return () => unsubscribeRealtime();
      } else {
        setRealtimeData(null);
        setLoading(false);
      }
    });

    return () => unsubscribeAuth();
  }, []);

  return { user, realtimeData, loading };
}

export function useRealtimeSession(sessionId: string) {
  const [sessionData, setSessionData] = useState<any>(null);

  useEffect(() => {
    if (!sessionId) return;

    const unsubscribe = subscribeRealtimeSessionData(sessionId, (data) => {
      setSessionData(data);
    });

    return () => unsubscribe();
  }, [sessionId]);

  const updateSession = (data: Record<string, any>) => {
    if (sessionId) {
      syncRealtimeSessionData(sessionId, data);
    }
  };

  return { sessionData, updateSession };
}
