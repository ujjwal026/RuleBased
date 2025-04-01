import { useState, useEffect, useRef } from "react";
import { FiSend } from "react-icons/fi";
import axios from "axios";

const ChatApp = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, type: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const response = await axios.post("http://localhost:5000/check_prompt", { prompt: input });
      const isBlocked = response.data.blocked;
      const botMessage = {
        text: isBlocked ? "Inappropriate Content Detected" : "✅ Accepted",
        type: isBlocked ? "error" : "accepted",
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error checking prompt:", error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      <header className="bg-green-700 text-white text-center py-4 text-xl font-semibold shadow-lg">
        AI Chat Filter
      </header>
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg w-fit max-w-xs ${
              msg.type === "user"
                ? "bg-gray-700 text-right self-end ml-auto"
                : msg.type === "accepted"
                ? "bg-green-500 text-left self-start"
                : "bg-gray-800 text-red-500 text-left self-start border border-red-500"
            }`}
          >
            {msg.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <footer className="bg-gray-800 p-4 flex items-center gap-2">
        <div className="flex-1 flex items-center bg-gray-900 border border-gray-600 rounded-lg px-3 py-2">
          <input
            type="text"
            className="flex-1 bg-transparent text-white focus:outline-none"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          />
        </div>
        <button
          className="bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-lg flex items-center justify-center"
          onClick={sendMessage}
        >
          <FiSend size={20} />
        </button>
      </footer>
    </div>
  );
};

export default ChatApp;
