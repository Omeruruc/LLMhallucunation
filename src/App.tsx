import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, RotateCcw, Settings2 } from 'lucide-react';
import { AgentSettings } from './components/AgentSettings';
import { ChatMessage } from './components/ChatMessage';
import { Message, AgentConfig, GlobalSettings } from './types';
import { fetchAgentResponse } from './utils/llmPipeline';

const AGENT_COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'];

function App() {
  // Bileşen içi durum; güncellenince React yeniden render eder.
  const [agents, setAgents] = useState<AgentConfig[]>([
    { number: 1, temperature: 1.8, color: AGENT_COLORS[0] },
    { number: 2, temperature: 1.2, color: AGENT_COLORS[1] },
    { number: 3, temperature: 0.6, color: AGENT_COLORS[2] },
    { number: 4, temperature: 0.2, color: AGENT_COLORS[3] },
  ]);

  const [globalSettings, setGlobalSettings] = useState<GlobalSettings>({
    maxTokens: 768,
    topP: 0.9,
  });

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  // Sohbet sonuna kaydırmak için DOM referansı; ref güncellemesi yeniden render tetiklemez.
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // İşlem sırasında bile güncel sıcaklıkları okumak için (kaydırıcı değişince state ile senkron).
  const agentsRef = useRef(agents);
  agentsRef.current = agents;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Mesaj listesi değişince en alta kaydır.
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Önceki state üzerinden güvenli güncelleme (functional update).
  const handleTemperatureChange = (agentNumber: number, newTemp: number) => {
    setAgents(prev =>
      prev.map(agent =>
        agent.number === agentNumber
          ? { ...agent, temperature: newTemp }
          : agent
      )
    );
  };

  // Ajanlar sırayla çalışır; isProcessing formu ve gönderimi kilitler.
  const processQuestion = async (question: string) => {
    setIsProcessing(true);

    try {
      const userMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: question,
      };
      setMessages(prev => [...prev, userMessage]);

      let previousResponse = '';

      // Önce “düşünüyor” satırı eklenir, cevap gelince aynı id ile güncellenir.
      const pipelineAgents = agentsRef.current;
      for (let i = 0; i < pipelineAgents.length; i++) {
        const agent = pipelineAgents[i];

        const thinkingMessage: Message = {
          id: `${Date.now()}-thinking-${i}`,
          type: 'agent',
          agentNumber: agent.number,
          content: '',
          color: agent.color,
          isThinking: true,
        };
        setMessages(prev => [...prev, thinkingMessage]);

        try {
          const response = await fetchAgentResponse(
            agent.number,
            question,
            previousResponse,
            agent.temperature,
            globalSettings.maxTokens,
            globalSettings.topP,
          );

          // Eşleşen mesajı değiştirip yeni dizi döndürür (immutable güncelleme).
          setMessages(prev =>
            prev.map(msg =>
              msg.id === thinkingMessage.id
                ? {
                    ...msg,
                    content: response,
                    isThinking: false,
                    hasCorrected: agent.number > 1,
                  }
                : msg
            )
          );

          previousResponse = response;
        } catch (err) {
          const detail = err instanceof Error ? err.message : String(err);
          setMessages(prev =>
            prev.map(msg =>
              msg.id === thinkingMessage.id
                ? {
                    ...msg,
                    content: `İstek başarısız: ${detail}`,
                    isThinking: false,
                    hasCorrected: false,
                  }
                : msg
            )
          );
          return;
        }
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // Sayfa yenilenmesini engeller (tek sayfa uygulaması).
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isProcessing) {
      processQuestion(inputValue.trim());
      setInputValue('');
    }
  };

  const resetChat = () => {
    setMessages([]);
  };

  // Tek kök eleman; stiller Tailwind className ile.
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-800">
              Çoklu LLM Halüsinasyon Filtreleme Sistemi
            </h1>
          </div>
          <p className="text-gray-600 ml-13">
            Dört aşamalı Gemini zinciri: taslak → düzeltme → ikinci düzeltme → nihai cevap.
            Her ajanın sıcaklığı aşağıdan API’ye iletilir.
          </p>
        </div>

        {/* Mobilde tek sütun; büyük ekranda 4 sütun (yan panel + sohbet). */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
              <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                Ajan Ayarları
              </h2>
              <p className="text-xs text-gray-600 mb-4">
                Temperature doğrudan Gemini isteğine gider; yüksek = daha yaratıcı (1), düşük = daha tutucu (4)
              </p>
            </div>

            {/* Global parametreler */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
              <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <Settings2 className="w-4 h-4 text-gray-500" />
                Global Parametreler
              </h2>

              {/* Max Tokens */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Max Tokens</span>
                  <span className="font-mono font-semibold text-gray-800">{globalSettings.maxTokens}</span>
                </div>
                <input
                  type="range"
                  min="256"
                  max="2048"
                  step="256"
                  value={globalSettings.maxTokens}
                  onChange={(e) =>
                    setGlobalSettings(prev => ({ ...prev, maxTokens: parseInt(e.target.value) }))
                  }
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>256</span>
                  <span>768</span>
                  <span>2048</span>
                </div>
                <p className="text-xs text-gray-500">Düşük tut → kredi tasarrufu</p>
              </div>

              {/* Top-P */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Top-P</span>
                  <span className="font-mono font-semibold text-gray-800">{globalSettings.topP.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={globalSettings.topP}
                  onChange={(e) =>
                    setGlobalSettings(prev => ({ ...prev, topP: parseFloat(e.target.value) }))
                  }
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-purple-500"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>0.10</span>
                  <span>0.50</span>
                  <span>1.00</span>
                </div>
                <p className="text-xs text-gray-500">Düşük = odaklı, yüksek = çeşitli kelime seçimi</p>
              </div>
            </div>

            {/* Liste öğelerinde stabil key. */}
            {agents.map(agent => (
              <AgentSettings
                key={agent.number}
                agentNumber={agent.number}
                temperature={agent.temperature}
                onTemperatureChange={(temp) =>
                  handleTemperatureChange(agent.number, temp)
                }
                color={agent.color}
              />
            ))}
          </div>

          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col h-[calc(100vh-200px)]">
              <div className="border-b border-gray-200 p-4 flex items-center justify-between">
                <div>
                  <h2 className="font-semibold text-gray-800">
                    Sohbet Akışı
                  </h2>
                  <p className="text-xs text-gray-600">
                    Ajanlar arası analiz ve düzeltme süreci
                  </p>
                </div>
                {messages.length > 0 && (
                  <button
                    onClick={resetChat}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Sıfırla
                  </button>
                )}
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {/* Mesaj yoksa boş durum, varsa liste. */}
                {messages.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <Sparkles className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p className="text-sm">
                        Bir soru sorarak başlayın
                      </p>
                      <p className="text-xs mt-1">
                        Ajanlar sırayla analiz edecek ve halüsinasyonları filtreleyecek
                      </p>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Mesaj alanlarını props olarak iletir. */}
                    {messages.map(message => (
                      <ChatMessage key={message.id} {...message} />
                    ))}
                    {/* scrollIntoView hedefi. */}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              <div className="border-t border-gray-200 p-4">
                {/* Kontrollü input: değer state’ten gelir, onChange ile güncellenir. */}
                <form onSubmit={handleSubmit} className="flex gap-2">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Bir soru sorun..."
                    disabled={isProcessing}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <button
                    type="submit"
                    disabled={isProcessing || !inputValue.trim()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2 font-medium"
                  >
                    {isProcessing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        İşleniyor
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        Gönder
                      </>
                    )}
                  </button>
                </form>
                {isProcessing && (
                  <p className="text-xs text-gray-500 mt-2">
                    Ajanlar sırayla analiz yapıyor...
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
