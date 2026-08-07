import { usePresets } from "../api/hooks";
import { activePresetId } from "../engine/levers";
import { useScenarioStore } from "../state/scenarioStore";

export function PresetBar() {
  const { data, isError } = usePresets();
  const levers = useScenarioStore((s) => s.levers);
  const applyPreset = useScenarioStore((s) => s.applyPreset);
  if (isError) return <div className="banner err">Presets no disponibles</div>;
  if (!data) return null;
  const active = activePresetId(levers);
  return (
    <div className="presets">
      {data.presets.map((p) => (
        <button
          key={p.id}
          type="button"
          className={p.id === active ? "ps on" : "ps"}
          onClick={() => applyPreset(p.id)}
        >
          {p.nm}
        </button>
      ))}
    </div>
  );
}
