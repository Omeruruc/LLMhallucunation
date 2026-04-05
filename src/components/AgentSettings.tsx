import { Thermometer } from 'lucide-react';

// Bileşenin dışarıdan aldığı props tipleri.

interface AgentSettingsProps {
  agentNumber: number;
  temperature: number;
  onTemperatureChange: (value: number) => void;
  color: string;
}

export function AgentSettings({
  agentNumber,
  temperature,
  onTemperatureChange,
  color,
}: AgentSettingsProps) {
  // Kendi state’i yok; sıcaklık App’te, değişiklik callback ile yukarı bildirilir.
  return (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
      <div className="flex items-center gap-2 mb-3">
        {/* Ajan rengi props’tan; dinamik hex için inline style. */}
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: color }}
        />
        <h3 className="font-semibold text-gray-800">Ajan {agentNumber}</h3>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1 text-gray-600">
            <Thermometer className="w-4 h-4" />
            <span>Temperature</span>
          </div>
          <span className="font-mono font-semibold text-gray-800">
            {temperature.toFixed(2)}
          </span>
        </div>

        {/* Değer üst bileşenden gelir; sürükleyince onTemperatureChange ile güncellenir. */}
        <input
          type="range"
          min="0"
          max="2"
          step="0.01"
          value={temperature}
          onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
          className="w-full h-2 rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, ${color} 0%, ${color} ${(temperature / 2) * 100}%, #e5e7eb ${(temperature / 2) * 100}%, #e5e7eb 100%)`,
          }}
        />

        <div className="flex justify-between text-xs text-gray-500">
          <span>0.00</span>
          <span>2.00</span>
        </div>
      </div>

      {/* Ajan numarasına göre kısa açıklama metni. */}
      <div className="mt-3 text-xs text-gray-600">
        {agentNumber === 1 &&
          "Cevap + zorunlu halüsinasyon/şüphe taraması (yapılandırılmış çıktı)"}
        {agentNumber === 2 &&
          "Ajan 1’i adım adım düzeltir; Düzeltilmiş cevap + şüpheli listesi"}
        {agentNumber === 3 &&
          "Ajan 2’yi adım adım düzeltir; ikinci tur birleşik metin"}
        {agentNumber === 4 &&
          "Sadece kullanıcıya gidecek nihai metin (iç süreç yok)"}
      </div>
    </div>
  );
}
