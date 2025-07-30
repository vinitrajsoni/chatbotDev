import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Mic, MicOff, Send, Play, Pause } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  text?: string;
  sender: "user" | "assistant";
  timestamp: Date;
  audioUrl?: string;
}

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
    null
  );
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentAudio = useRef<HTMLAudioElement | null>(null);
  const { toast } = useToast();

  const API_BASE_URL = "http://localhost:8000";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    // 👇 Trigger deletion of all static files
    fetch("http://localhost:8000/clear-static", {
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("Static folder cleared:", data.deleted);
      })
      .catch((err) => {
        console.error("Failed to clear static folder:", err);
      });
  }, []);

  useEffect(() => {
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      text: "Hi, how can I help you today?",
      sender: "assistant",
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  }, []);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");

    try {
      const res = await fetch(`${API_BASE_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: inputText }),
      });

      const data = await res.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || "No response received.",
        sender: "assistant",
        timestamp: new Date(),
        audioUrl: data.voice_output || undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          text: "⚠️ Failed to connect to server.",
          sender: "assistant",
          timestamp: new Date(),
        },
      ]);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const audioChunks: BlobPart[] = [];

      recorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        const audioUrl = URL.createObjectURL(audioBlob);

        const userMessage: Message = {
          id: Date.now().toString(),
          text: "🎤 Voice message",
          sender: "user",
          timestamp: new Date(),
          audioUrl,
        };

        setMessages((prev) => [...prev, userMessage]);

        try {
          const formData = new FormData();
          formData.append("file", audioBlob, "voice.wav");

          const res = await fetch(`${API_BASE_URL}/ask-voice`, {
            method: "POST",
            body: formData,
          });

          const data = await res.json();

          const assistantTextMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: data.response || "No response received.",
            sender: "assistant",
            timestamp: new Date(),
          };

          const assistantVoiceMessage: Message = {
            id: (Date.now() + 2).toString(),
            sender: "assistant",
            text: "🔊 Voice response",
            audioUrl: data.voice_output || undefined,
            timestamp: new Date(),
          };

          setMessages((prev) => [
            ...prev,
            assistantTextMessage,
            assistantVoiceMessage,
          ]);
        } catch (err) {
          setMessages((prev) => [
            ...prev,
            {
              id: (Date.now() + 3).toString(),
              text: "⚠️ Failed to process voice input.",
              sender: "assistant",
              timestamp: new Date(),
            },
          ]);
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);

      toast({
        title: "Recording started",
        description: "Speak your message now...",
      });
    } catch (error) {
      toast({
        title: "Recording failed",
        description: "Please allow microphone access.",
        variant: "destructive",
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      setMediaRecorder(null);
      setIsRecording(false);

      toast({
        title: "Recording stopped",
        description: "Sending your voice message...",
      });
    }
  };

  const playAudio = (audioUrl: string, messageId: string) => {
    // Stop if same message is playing
    if (playingMessageId === messageId) {
      currentAudio.current?.pause();
      currentAudio.current?.currentTime &&
        (currentAudio.current.currentTime = 0);
      currentAudio.current = null;
      setPlayingMessageId(null);
      return;
    }

    // Stop previously playing audio
    if (currentAudio.current) {
      currentAudio.current.pause();
      currentAudio.current.currentTime = 0;
      currentAudio.current = null;
    }

    const audio = new Audio(audioUrl);
    audio.crossOrigin = "anonymous";
    currentAudio.current = audio;
    audio.play().catch((err) => console.warn("Playback failed:", err));
    setPlayingMessageId(messageId);

    audio.onended = () => {
      setPlayingMessageId(null);
      currentAudio.current = null;
    };
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-white flex flex-col">
      <div className="bg-gradient-to-r from-orange-400/20 to-orange-500/30 backdrop-blur-md border-b border-orange-200/50 p-4 shadow-lg">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <img
            src="/lovable-uploads/e462fbbb-cb09-4a4c-9025-c5a371c51ddf.png"
            alt="Munafa Virtual Assistant"
            className="w-10 h-10 object-contain drop-shadow-sm"
          />
          <div>
            <h1 className="text-xl font-bold text-gray-900 drop-shadow-sm">
              Munafa Virtual Assistant
            </h1>
            <p className="text-sm text-gray-700">Your AI-powered chat buddy</p>
          </div>
        </div>
      </div>

      <div className="flex-1 max-w-4xl mx-auto w-full p-4 flex flex-col">
        <div className="flex-1 space-y-4 mb-4 overflow-y-auto max-h-[calc(100vh-200px)]">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-xs sm:max-w-md p-4 rounded-2xl shadow-sm ${
                  message.sender === "user"
                    ? "bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-br-md"
                    : "bg-white border border-orange-100 text-gray-800 rounded-bl-md"
                }`}
              >
                <div className="space-y-2">
                  {message.text && (
                    <p className="text-sm leading-relaxed">{message.text}</p>
                  )}
                  {message.audioUrl && (
                    <div className="flex items-center gap-2 mt-3">
                      <Button
                        size="sm"
                        variant={
                          message.sender === "user" ? "secondary" : "outline"
                        }
                        onClick={() => playAudio(message.audioUrl!, message.id)}
                        className="h-8 w-8 p-0 bg-white/20 hover:bg-white/30 border-white/30"
                      >
                        {playingMessageId === message.id ? (
                          <Pause className="h-3 w-3" />
                        ) : (
                          <Play className="h-3 w-3" />
                        )}
                      </Button>
                      <span className="text-xs opacity-75">Voice message</span>
                    </div>
                  )}
                </div>
                <p
                  className={`text-xs mt-2 ${
                    message.sender === "user"
                      ? "text-orange-100"
                      : "text-gray-500"
                  }`}
                >
                  {formatTime(message.timestamp)}
                </p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <Card className="p-4 bg-white border-orange-100 shadow-lg">
          <div className="flex gap-2">
            <Input
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Type your message..."
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              className="flex-1 border-orange-200 focus:border-orange-400 focus:ring-orange-400"
            />
            <Button
              onClick={isRecording ? stopRecording : startRecording}
              variant={isRecording ? "destructive" : "outline"}
              size="icon"
              className={`border-orange-300 hover:border-orange-400 ${
                isRecording
                  ? "animate-pulse bg-red-500 hover:bg-red-600"
                  : "hover:bg-orange-50"
              }`}
            >
              {isRecording ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4 text-orange-600" />
              )}
            </Button>

            <Button
              onClick={handleSendMessage}
              disabled={!inputText.trim()}
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 shadow-lg"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Index;
