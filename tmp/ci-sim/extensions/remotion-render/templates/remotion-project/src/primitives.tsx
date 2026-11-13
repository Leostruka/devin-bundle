import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

const CENTER: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
};

export const KineticText: React.FC<{ text: string; size?: number }> = ({
  text,
  size = 96,
}) => (
  <AbsoluteFill style={CENTER}>
    <div
      style={{
        color: "#f0f6fc",
        fontSize: size,
        fontWeight: 700,
        fontFamily: "system-ui, sans-serif",
        textAlign: "center",
        padding: "0 8%",
        lineHeight: 1.15,
      }}
    >
      {text}
    </div>
  </AbsoluteFill>
);

export const DiagramNodes: React.FC<{ nodes: { label: string }[] }> = ({
  nodes,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ ...CENTER, gap: 40 }}>
      {nodes.map((n, i) => {
        const s = interpolate(frame, [i * 6, i * 6 + 12], [0, 1], {
          extrapolateRight: "clamp",
        });
        return (
          <div
            key={i}
            style={{
              opacity: s,
              transform: `scale(${0.7 + 0.3 * s})`,
              border: "2px solid #58a6ff",
              borderRadius: 16,
              color: "#f0f6fc",
              fontSize: 42,
              padding: "24px 32px",
              fontFamily: "system-ui, sans-serif",
            }}
          >
            {n.label}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

export const Counter: React.FC<{ to: number; label?: string }> = ({
  to,
  label,
}) => {
  const frame = useCurrentFrame();
  const v = Math.round(interpolate(frame, [0, 30], [0, to], {
    extrapolateRight: "clamp",
  }));
  return (
    <AbsoluteFill style={{ ...CENTER, flexDirection: "column" }}>
      <div
        style={{
          color: "#58a6ff",
          fontSize: 220,
          fontWeight: 800,
          fontVariantNumeric: "tabular-nums",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        {v}
      </div>
      {label ? (
        <div style={{ color: "#8b949e", fontSize: 48 }}>{label}</div>
      ) : null}
    </AbsoluteFill>
  );
};

export const PanZoom: React.FC<{ src: string; zoom?: number }> = ({
  src,
  zoom = 1.15,
}) => {
  const frame = useCurrentFrame();
  const z = interpolate(frame, [0, 90], [1, zoom], {
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <img
        src={src}
        style={{ width: "100%", height: "100%", objectFit: "cover",
                 transform: `scale(${z})` }}
      />
    </AbsoluteFill>
  );
};
