import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react"; // Import useRef along with other hooks

import LoginPage from "./pages/LoginPage";
import ChatApp from "./pages/ChatApp";

const App = () => {
  const [user, setUser] = useState(null);

  // Check if the user is already logged in from localStorage
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  // Handle login and save user data to localStorage
  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData)); // Persist user login state
  };

  // Handle logout and remove user data from localStorage
  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem("user"); // Clear user data from localStorage
  };

  return (
    <Router>
      <Routes>
        {/* Route for the login page */}
        <Route
          path="/"
          element={user ? <Navigate to="/chat" /> : <LoginPage onLogin={handleLogin} />}
        />

        {/* Route for the chat page */}
        <Route
          path="/chat"
          element={user ? <ChatApp user={user} onLogout={handleLogout} /> : <Navigate to="/" />}
        />

        {/* Default route (redirect to login page if route not found) */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
};

export default App;
