import { Composition } from "remotion";
import { PlanComposition } from "./PlanComposition";
import plan from "./plan.json";

export const RemotionRoot: React.FC = () => {
  const fps = (plan as { fps?: number }).fps ?? 30;
  const [w, h] = (plan as { size?: [number, number] }).size ?? [1920, 1080];
  const beats = (plan as { beats: { sync_range: [number, number] }[] })
    .beats ?? [];
  const duration = Math.max(
    1,
    Math.ceil(Math.max(...beats.map((b) => b.sync_range[1]), 1) * fps)
  );
  return (
    <Composition
      id="Plan"
      component={PlanComposition}
      durationInFrames={duration}
      fps={fps}
      width={w}
      height={h}
    />
  );
};
