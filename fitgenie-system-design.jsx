import { useState, useEffect } from "react";

const agents = [
  {
    id: "orchestrator",
    label: "Orchestrator",
    sub: "调度 & 决策核心",
    icon: "⚡",
    color: "#f59e0b",
    glow: "#f59e0b",
    x: 50,
    y: 10,
    desc: "调度所有 Agent 的执行顺序，处理冲突（如训练强度 vs 热量缺口），维护全局任务状态。",
    connects: ["coach", "diet", "mental", "tracker", "analyst"],
    detail: [
      "Rule-based arbitration：优先级加权裁决",
      "DAG 执行图：确保数据流无循环依赖",
      "异常捕获：单个 Agent 失败不影响全局",
    ],
  },
  {
    id: "coach",
    label: "Coach Agent",
    sub: "训练规划",
    icon: "🏋️",
    color: "#3b82f6",
    glow: "#3b82f6",
    x: 10,
    y: 45,
    desc: "根据用户体能水平生成每日训练计划，实现渐进式负荷（Progressive Overload）。",
    connects: ["memory"],
    detail: [
      "输入：体能档案 + 历史表现",
      "输出：JSON 格式训练计划",
      "策略：周期化训练（线性 → 波浪式）",
    ],
  },
  {
    id: "diet",
    label: "Diet Agent",
    sub: "饮食管理",
    icon: "🥗",
    color: "#10b981",
    glow: "#10b981",
    x: 30,
    y: 45,
    desc: "计算 BMR → TDEE，制定热量缺口策略，输出宏量营养素分配方案。",
    connects: ["memory"],
    detail: [
      "Mifflin-St Jeor 公式计算 BMR",
      "蛋白质优先策略（2.2g/kg）",
      "热量缺口控制在 300–500 kcal/day",
    ],
  },
  {
    id: "mental",
    label: "Mental Agent",
    sub: "行为 & 心理",
    icon: "🧠",
    color: "#8b5cf6",
    glow: "#8b5cf6",
    x: 55,
    y: 45,
    desc: "分析用户坚持率与情绪状态，生成个性化激励话术，提升 Adherence（长期坚持率）。",
    connects: ["memory"],
    detail: [
      "检测连续打卡断链（≥2天）",
      "基于完成率调整激励力度",
      "模拟真实教练语言风格",
    ],
  },
  {
    id: "tracker",
    label: "Tracker Agent",
    sub: "数据采集",
    icon: "📊",
    color: "#f43f5e",
    glow: "#f43f5e",
    x: 75,
    y: 45,
    desc: "标准化用户输入（体重、步数、饮食、训练完成情况），写入短期记忆层。",
    connects: ["memory"],
    detail: [
      "输入：自然语言 / 结构化表单",
      "输出：标准化 JSON 数据包",
      "支持：可穿戴设备 API 扩展",
    ],
  },
  {
    id: "analyst",
    label: "Analyst Agent",
    sub: "分析 & 优化",
    icon: "📈",
    color: "#06b6d4",
    glow: "#06b6d4",
    x: 90,
    y: 45,
    desc: "检测减脂停滞（Plateau）：若7天内体重变化 < 0.2kg，触发计划调整。",
    connects: ["memory"],
    detail: [
      "滑动窗口分析（7天/14天）",
      "Plateau 检测阈值：<0.2kg/week",
      "输出结构化调整建议给 Orchestrator",
    ],
  },
  {
    id: "memory",
    label: "Memory Layer",
    sub: "短期 + 长期记忆",
    icon: "💾",
    color: "#64748b",
    glow: "#94a3b8",
    x: 50,
    y: 80,
    desc: "双层记忆架构：短期存近7天数据（SQLite），长期用向量数据库（Chroma）存储用户习惯与历史策略。",
    connects: [],
    detail: [
      "Short-term：Redis / SQLite，7天滚动窗口",
      "Long-term：Chroma 向量库 + Embedding",
      "Retrieval：相似情境策略召回",
    ],
  },
];

const FLOW_STEPS = [
  { ids: ["tracker"], label: "① Tracker 收集今日数据" },
  { ids: ["analyst"], label: "② Analyst 检测趋势 / Plateau" },
  { ids: ["coach", "diet"], label: "③ Coach + Diet 生成新计划" },
  { ids: ["mental"], label: "④ Mental 输出激励反馈" },
  { ids: ["memory"], label: "⑤ Memory 更新长期档案" },
];

export default function FitGenie() {
  const [selected, setSelected] = useState(null);
  const [flowStep, setFlowStep] = useState(-1);
  const [playing, setPlaying] = useState(false);
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    let timer;
    if (playing) {
      if (flowStep < FLOW_STEPS.length - 1) {
        timer = setTimeout(() => setFlowStep((s) => s + 1), 1200);
      } else {
        timer = setTimeout(() => {
          setPlaying(false);
          setFlowStep(-1);
        }, 1800);
      }
    }
    return () => clearTimeout(timer);
  }, [playing, flowStep]);

  const startFlow = () => {
    setSelected(null);
    setFlowStep(0);
    setPlaying(true);
  };

  const isFlowActive = (id) => {
    if (flowStep < 0) return false;
    return FLOW_STEPS.slice(0, flowStep + 1).some((s) => s.ids.includes(id));
  };

  const isCurrentStep = (id) => {
    if (flowStep < 0) return false;
    return FLOW_STEPS[flowStep]?.ids.includes(id);
  };

  const selectedAgent = agents.find((a) => a.id === selected);

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #020617 0%, #0a0f1e 50%, #050d1a 100%)",
      fontFamily: "'DM Mono', 'Fira Code', monospace",
      color: "#e2e8f0",
      display: "flex",
      flexDirection: "column",
      padding: "0",
      overflow: "hidden",
    }}>
      {/* Grid overlay */}
      <div style={{
        position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0,
        backgroundImage: `
          linear-gradient(rgba(148,163,184,0.04) 1px, transparent 1px),
          linear-gradient(90deg, rgba(148,163,184,0.04) 1px, transparent 1px)
        `,
        backgroundSize: "40px 40px",
      }} />

      {/* Header */}
      <div style={{
        position: "relative", zIndex: 10,
        padding: "20px 32px 12px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 22 }}>🏋️</span>
            <span style={{
              fontSize: 20, fontWeight: 700, letterSpacing: "0.15em",
              background: "linear-gradient(90deg, #f59e0b, #fbbf24)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            }}>FITGENIE</span>
            <span style={{
              fontSize: 10, padding: "2px 8px", borderRadius: 4,
              border: "1px solid rgba(245,158,11,0.4)",
              color: "#f59e0b", letterSpacing: "0.1em",
            }}>SYSTEM DESIGN</span>
          </div>
          <div style={{ fontSize: 11, color: "#475569", marginTop: 4, letterSpacing: "0.05em" }}>
            Multi-Agent Personalized Fitness Coaching System
          </div>
        </div>
        <button
          onClick={startFlow}
          disabled={playing}
          style={{
            padding: "8px 18px", borderRadius: 6,
            border: "1px solid rgba(245,158,11,0.5)",
            background: playing ? "rgba(245,158,11,0.05)" : "rgba(245,158,11,0.12)",
            color: playing ? "#78350f" : "#f59e0b",
            cursor: playing ? "not-allowed" : "pointer",
            fontSize: 12, letterSpacing: "0.08em",
            transition: "all 0.2s",
          }}
        >
          {playing ? "▶ Running..." : "▶ Run Daily Loop"}
        </button>
      </div>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Main diagram */}
        <div style={{ flex: 1, position: "relative", zIndex: 5 }}>

          {/* Orchestrator */}
          <AgentNode
            agent={agents[0]}
            active={isFlowActive("orchestrator")}
            current={isCurrentStep("orchestrator")}
            selected={selected === "orchestrator"}
            hovered={hovered === "orchestrator"}
            onClick={() => setSelected(selected === "orchestrator" ? null : "orchestrator")}
            onHover={setHovered}
            style={{ top: "8%", left: "50%", transform: "translateX(-50%)" }}
            size="lg"
          />

          {/* Arm connections from Orchestrator */}
          <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none", zIndex: 1 }}>
            {[
              { x1: "50%", y1: "14%", x2: "14%", y2: "44%" },
              { x1: "50%", y1: "14%", x2: "33%", y2: "44%" },
              { x1: "50%", y1: "14%", x2: "57%", y2: "44%" },
              { x1: "50%", y1: "14%", x2: "78%", y2: "44%" },
              { x1: "50%", y1: "14%", x2: "92%", y2: "44%" },
            ].map((line, i) => (
              <line key={i}
                x1={line.x1} y1={line.y1} x2={line.x2} y2={line.y2}
                stroke="rgba(245,158,11,0.2)" strokeWidth="1.5"
                strokeDasharray="4 4"
              />
            ))}
            {/* Memory connections */}
            {[
              { x1: "14%", y1: "56%", x2: "50%", y2: "78%" },
              { x1: "33%", y1: "56%", x2: "50%", y2: "78%" },
              { x1: "57%", y1: "56%", x2: "50%", y2: "78%" },
              { x1: "78%", y1: "56%", x2: "50%", y2: "78%" },
              { x1: "92%", y1: "56%", x2: "50%", y2: "78%" },
            ].map((line, i) => (
              <line key={`m${i}`}
                x1={line.x1} y1={line.y1} x2={line.x2} y2={line.y2}
                stroke="rgba(100,116,139,0.25)" strokeWidth="1"
                strokeDasharray="3 6"
              />
            ))}
          </svg>

          {/* Sub agents row */}
          {agents.slice(1, 6).map((agent, i) => {
            const lefts = ["8%", "27%", "52%", "70%", "87%"];
            return (
              <AgentNode
                key={agent.id}
                agent={agent}
                active={isFlowActive(agent.id)}
                current={isCurrentStep(agent.id)}
                selected={selected === agent.id}
                hovered={hovered === agent.id}
                onClick={() => setSelected(selected === agent.id ? null : agent.id)}
                onHover={setHovered}
                style={{ top: "42%", left: lefts[i], transform: "translateX(-50%)" }}
              />
            );
          })}

          {/* Memory node */}
          <AgentNode
            agent={agents[6]}
            active={isFlowActive("memory")}
            current={isCurrentStep("memory")}
            selected={selected === "memory"}
            hovered={hovered === "memory"}
            onClick={() => setSelected(selected === "memory" ? null : "memory")}
            onHover={setHovered}
            style={{ top: "74%", left: "50%", transform: "translateX(-50%)" }}
            size="lg"
          />

          {/* Flow steps timeline */}
          {flowStep >= 0 && (
            <div style={{
              position: "absolute", bottom: 16, left: "50%", transform: "translateX(-50%)",
              display: "flex", gap: 6, alignItems: "center",
              background: "rgba(2,6,23,0.9)", padding: "8px 16px",
              borderRadius: 8, border: "1px solid rgba(255,255,255,0.08)",
              backdropFilter: "blur(8px)", zIndex: 20,
            }}>
              {FLOW_STEPS.map((step, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: "50%",
                    background: i <= flowStep ? "#f59e0b" : "rgba(255,255,255,0.1)",
                    boxShadow: i === flowStep ? "0 0 8px #f59e0b" : "none",
                    transition: "all 0.4s",
                  }} />
                  {i === flowStep && (
                    <span style={{ fontSize: 11, color: "#f59e0b", whiteSpace: "nowrap" }}>
                      {step.label}
                    </span>
                  )}
                  {i < FLOW_STEPS.length - 1 && (
                    <div style={{ width: 16, height: 1, background: i < flowStep ? "#f59e0b" : "rgba(255,255,255,0.1)", transition: "all 0.4s" }} />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Side panel */}
        <div style={{
          width: selectedAgent ? 280 : 0,
          overflow: "hidden",
          transition: "width 0.35s cubic-bezier(0.4,0,0.2,1)",
          borderLeft: selectedAgent ? "1px solid rgba(255,255,255,0.07)" : "none",
          background: "rgba(2,6,23,0.8)",
          backdropFilter: "blur(16px)",
          zIndex: 20,
          flexShrink: 0,
        }}>
          {selectedAgent && (
            <div style={{ padding: "24px 20px", width: 280 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                <span style={{ fontSize: 28 }}>{selectedAgent.icon}</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, color: selectedAgent.color }}>
                    {selectedAgent.label}
                  </div>
                  <div style={{ fontSize: 11, color: "#475569" }}>{selectedAgent.sub}</div>
                </div>
              </div>

              <div style={{
                padding: "12px", borderRadius: 8,
                background: `${selectedAgent.color}0d`,
                border: `1px solid ${selectedAgent.color}22`,
                fontSize: 12, lineHeight: 1.7, color: "#94a3b8",
                marginBottom: 16,
              }}>
                {selectedAgent.desc}
              </div>

              <div style={{ fontSize: 11, color: "#475569", marginBottom: 8, letterSpacing: "0.1em" }}>
                KEY SPECS
              </div>
              {selectedAgent.detail.map((d, i) => (
                <div key={i} style={{
                  display: "flex", gap: 8, marginBottom: 8, alignItems: "flex-start",
                }}>
                  <div style={{
                    width: 4, height: 4, borderRadius: "50%",
                    background: selectedAgent.color,
                    marginTop: 6, flexShrink: 0,
                  }} />
                  <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.6 }}>{d}</div>
                </div>
              ))}

              {/* Tech tag */}
              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 11, color: "#475569", marginBottom: 8, letterSpacing: "0.1em" }}>
                  IMPLEMENTATION
                </div>
                {[
                  selectedAgent.id === "orchestrator" && "LangGraph StateGraph",
                  selectedAgent.id === "coach" && "GPT-4 + Tool Call",
                  selectedAgent.id === "diet" && "GPT-4 + Python Logic",
                  selectedAgent.id === "mental" && "GPT-4 Few-shot",
                  selectedAgent.id === "tracker" && "FastAPI Endpoint",
                  selectedAgent.id === "analyst" && "Pandas + LLM",
                  selectedAgent.id === "memory" && "Chroma + SQLite",
                ].filter(Boolean).map((tag) => (
                  <span key={tag} style={{
                    display: "inline-block", padding: "3px 10px",
                    borderRadius: 4, background: `${selectedAgent.color}18`,
                    border: `1px solid ${selectedAgent.color}30`,
                    color: selectedAgent.color, fontSize: 11, marginRight: 4,
                  }}>{tag}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div style={{
        position: "relative", zIndex: 10,
        padding: "10px 32px",
        borderTop: "1px solid rgba(255,255,255,0.05)",
        display: "flex", gap: 24, alignItems: "center",
      }}>
        <span style={{ fontSize: 10, color: "#334155", letterSpacing: "0.1em" }}>CLICK ANY NODE TO INSPECT</span>
        {[
          { color: "rgba(245,158,11,0.5)", label: "Orchestrator links", dash: "4 4" },
          { color: "rgba(100,116,139,0.4)", label: "Memory writes", dash: "3 6" },
        ].map(({ color, label, dash }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <svg width="24" height="8">
              <line x1="0" y1="4" x2="24" y2="4" stroke={color} strokeWidth="1.5" strokeDasharray={dash} />
            </svg>
            <span style={{ fontSize: 10, color: "#334155" }}>{label}</span>
          </div>
        ))}
        <div style={{ marginLeft: "auto", fontSize: 10, color: "#1e293b" }}>
          LangGraph · FastAPI · Chroma · SQLite
        </div>
      </div>
    </div>
  );
}

function AgentNode({ agent, active, current, selected, hovered, onClick, onHover, style, size = "sm" }) {
  const isLg = size === "lg";
  const isOn = active || selected || hovered;

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => onHover(agent.id)}
      onMouseLeave={() => onHover(null)}
      style={{
        position: "absolute",
        width: isLg ? 140 : 110,
        cursor: "pointer",
        zIndex: 10,
        transition: "transform 0.2s",
        transform: `${style.transform || ""} ${(hovered || selected) ? "scale(1.05)" : "scale(1)"}`,
        ...style,
      }}
    >
      <div style={{
        borderRadius: isLg ? 12 : 10,
        border: `1.5px solid ${current ? agent.color : selected ? `${agent.color}90` : `${agent.color}28`}`,
        background: current
          ? `${agent.color}15`
          : selected
          ? `${agent.color}0e`
          : "rgba(15,23,42,0.8)",
        padding: isLg ? "14px 16px" : "10px 12px",
        backdropFilter: "blur(8px)",
        boxShadow: current
          ? `0 0 20px ${agent.glow}50, 0 0 40px ${agent.glow}20, inset 0 0 20px ${agent.glow}08`
          : selected
          ? `0 0 12px ${agent.glow}30`
          : hovered
          ? `0 0 8px ${agent.glow}20`
          : "none",
        transition: "all 0.3s",
      }}>
        <div style={{ fontSize: isLg ? 22 : 18, marginBottom: 4 }}>{agent.icon}</div>
        <div style={{
          fontSize: isLg ? 13 : 11, fontWeight: 700,
          color: isOn ? agent.color : "#94a3b8",
          transition: "color 0.3s",
          letterSpacing: "0.02em",
        }}>
          {agent.label}
        </div>
        <div style={{ fontSize: 10, color: "#475569", marginTop: 2 }}>
          {agent.sub}
        </div>
        {current && (
          <div style={{
            marginTop: 6, display: "flex", alignItems: "center", gap: 4,
          }}>
            <div style={{
              width: 6, height: 6, borderRadius: "50%",
              background: agent.color,
              animation: "none",
              boxShadow: `0 0 6px ${agent.color}`,
            }} />
            <span style={{ fontSize: 9, color: agent.color, letterSpacing: "0.05em" }}>ACTIVE</span>
          </div>
        )}
      </div>
    </div>
  );
}
