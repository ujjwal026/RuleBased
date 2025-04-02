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
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 p-4 border-b border-gray-700 flex items-center justify-center">
        <h1 className="text-xl font-medium text-gray-100"> Chat </h1>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-12">
              <p className="text-lg">No messages yet</p>
              <p className="text-sm mt-2">Type a message to get started</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className="flex">
                <div
                  className={`p-3 rounded-lg w-fit max-w-md ${
                    msg.type === "user"
                      ? "bg-gray-700 text-gray-100 ml-auto"
                      : msg.type === "accepted"
                      ? "bg-green-500 text-left self-start"
                      : "bg-gray-800 text-red-500 border border-red-500"
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <footer className="bg-gray-800 border-t border-gray-700 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="flex-1 border border-gray-600 rounded-lg bg-gray-800 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
              <textarea
                className="w-full px-5 py-4 text-gray-100 bg-gray-800 resize-none focus:outline-none rounded-lg text-lg"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendMessage())}
                rows={2}
                style={{ minHeight: "60px", maxHeight: "200px" }}
              />
            </div>
            <button
              className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full flex items-center justify-center disabled:opacity-50"
              onClick={sendMessage}
              disabled={!input.trim()}
            >
              <FiSend size={24} />
            </button>
          </div>
          <div className="text-sm text-gray-400 mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ChatApp;