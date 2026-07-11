"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import axios from "axios";


const ApiContext = createContext(null);

const BASE_URL = "http://127.0.0.1:8000";


export function ApiProvider({ children }) {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Legacy compatibility value.
  // Keep temporarily because older canvas code may expect apiKey.
  const apiKey = "local-prana-engine";


  const fetchUserData = useCallback(async () => {
    try {
      const { data } = await axios.get(
        `${BASE_URL}/api/v1/creative-agent/account/balance`
      );

      setUserData({
        username:
          data.email?.split("@")[0] ||
          "PRANA User",

        balance:
          data.balance ?? 0,

        email:
          data.email ?? null,
      });
    } catch (err) {
      console.warn(
        "Legacy account endpoint unavailable:",
        err
      );

      // Local-first fallback for PRANA.
      setUserData({
        username: "PRANA User",
        balance: 0,
        email: null,
      });
    } finally {
      setLoading(false);
    }
  }, []);


  useEffect(() => {
    const timerId = window.setTimeout(() => {
      void fetchUserData();
    }, 0);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [fetchUserData]);


  return (
    <ApiContext.Provider
      value={{
        apiKey,
        userData,
        loading,
        fetchUserData,
      }}
    >
      {children}
    </ApiContext.Provider>
  );
}


export function useApi() {
  const context = useContext(ApiContext);

  if (!context) {
    throw new Error(
      "useApi must be used inside ApiProvider"
    );
  }

  return context;
}