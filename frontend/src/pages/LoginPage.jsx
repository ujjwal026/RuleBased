import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const LoginPage = ({ onLogin }) => { // ✅ Accept the onLogin prop
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    try {
      const response = await axios.post("http://localhost:5000/login", {
        username,
        password,
      });

      console.log("Login response:", response);

      if (response.data.success) {
        const userData = {
          username,
          role: response.data.role,
        };

        onLogin(userData); // ✅ Call onLogin with userData
        navigate("/chat"); // ✅ Navigate to chat
      }
    } catch (error) {
      if (error.response && error.response.status === 401) {
        setErrorMessage(error.response.data.message);
      } else {
        setErrorMessage("Error logging in. Please try again.");
      }
      console.error("Login error:", error);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-900 text-white">
      {/* Left Side - Slogan */}
      <div className="hidden md:flex flex-col justify-center items-start w-full md:w-1/2 bg-gradient-to-r from-blue-700 via-purple-700 to-indigo-800 text-white px-10 py-12">
        <h2 className="text-4xl font-bold mb-4">Securing LLMs with Confidence</h2>
        <p className="text-lg mb-6">
          Protecting the future of AI by ensuring secure and trusted language models for every interaction.
        </p>
        <p className="text-sm italic">"Your data, your AI, our responsibility."</p>
      </div>

      {/* Right Side - Form */}
      <div className="flex flex-col justify-center items-center w-full md:w-1/2 max-w-md mx-auto p-6 bg-gray-800 rounded-lg shadow-xl mt-20 mb-12">
        <h2 className="text-3xl font-semibold text-white mb-8">Login</h2>
        <form onSubmit={handleLogin} className="w-full space-y-6">
          <div>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-5 py-4 rounded-md bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-all"
              required
            />
          </div>
          <div>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-5 py-4 rounded-md bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-all"
              required
            />
          </div>
          {errorMessage && <p className="text-red-500 text-sm">{errorMessage}</p>}
          <button
            type="submit"
            className="w-full py-3 bg-blue-600 rounded-md text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
