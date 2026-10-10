import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Counter, DiagramNodes, KineticText, PanZoom } from "./primitives";
import plan from "./plan.json";

type Motion = {
  easing?: "linear" | "spring" | "easeOut";
  enter?: "fade" | "slideUp" | "scale" | "none";
  exit?: "fade" | "none";
  enter_s?: number;
  exit_s?: number;
};
type Beat = {
  id: string;
  sync_range: [number, number];
  visual: { type: string; props?: Record<string, unknown> };
  motion_spec?: Motion;
  overlay?: boolean;
};

const enterStyle = (
  frame: number,
  fps: number,
  spec: Motion,
): React.CSSProperties => {
  const d = Math.max(1, (spec.enter_s ?? 0.4) * fps);
  const t = interpolate(frame, [0, d], [0, 1], {
    extrapolateRight: "clamp",
  });
  const s =
    spec.easing === "spring"
      ? spring({ frame, fps, config: { damping: 18 } })
      : t;
  switch (spec.enter ?? "fade") {
    case "slideUp":
      return { opacity: t, transform: `translateY(${(1 - s) * 40}px)` };
    case "scale":
      return { opacity: t, transform: `scale(${0.8 + 0.2 * s})` };
    case "none":
      return {};
    default:
      return { opacity: t };
  }
};

const BeatView: React.FC<{ beat: Beat }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const spec = beat.motion_spec ?? {};
  const style = enterStyle(frame, fps, spec);
  const p = beat.visual.props ?? {};
  let body: React.ReactNode = null;
  switch (beat.visual.type) {
    case "kinetic_text":
      body = <KineticText {...(p as { text: string; size?: number })} />;
      break;
    case "diagram_nodes":
      body = <DiagramNodes {...(p as { nodes: { label: string }[] })} />;
      break;
    case "counter":
      body = <Counter {...(p as { to: number; label?: string })} />;
      break;
    case "pan_zoom":
      body = <PanZoom {...(p as { src: string; zoom?: number })} />;
      break;
    default:
      body = <KineticText text={String(p.text ?? beat.visual.type)} />;
  }
  return <AbsoluteFill style={style}>{body}</AbsoluteFill>;
};

export const PlanComposition: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#0d1117" }}>
      {(plan.beats as Beat[]).map((b) => (
        <Sequence
          key={b.id}
          from={Math.floor(b.sync_range[0] * fps)}
          durationInFrames={Math.max(
            1,
            Math.ceil((b.sync_range[1] - b.sync_range[0]) * fps)
          )}
        >
          <BeatView beat={b} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
