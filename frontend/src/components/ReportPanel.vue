<template>
  <div class="report-panel">
    <!-- 头部：标题 + 总分环 -->
    <div class="report-head">
      <div class="report-title-box">
        <div class="report-kicker">模拟面试 · 总结报告</div>
        <div class="report-title">面试评估报告</div>
        <div class="report-sub">基于你的回答生成的综合评估，可下载完整报告</div>
      </div>
      <div class="score-ring" v-if="parsed.score != null">
        <svg viewBox="0 0 120 120" class="ring-svg">
          <defs>
            <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stop-color="var(--brand)" />
              <stop offset="100%" stop-color="var(--brand-light)" />
            </linearGradient>
          </defs>
          <circle class="ring-bg" cx="60" cy="60" r="52" />
          <circle
            class="ring-fg"
            cx="60"
            cy="60"
            r="52"
            stroke="url(#ringGrad)"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="ringOffset"
          />
        </svg>
        <div class="score-num">{{ parsed.score }}</div>
        <div class="score-total">/ 100</div>
      </div>
    </div>

    <!-- 无结构化数据（旧会话）：仅展示报告原文，前端不做二次解析（bug #29） -->
    <div v-if="parsed.raw" class="report-raw">{{ report }}</div>

    <!-- 维度评分 -->
    <div v-if="parsed.dimensions.length" class="report-section">
      <div class="section-title">
        <span class="dot dot-dim"></span>维度评分
      </div>
      <div v-for="d in parsed.dimensions" :key="d.label" class="dim-row">
        <span class="dim-label" :title="d.label">{{ d.label }}</span>
        <div class="dim-track">
          <div
            class="dim-fill"
            :style="{ width: d.score + '%', background: dimColor(d.score) }"
          ></div>
        </div>
        <span class="dim-score">{{ d.score }}</span>
      </div>
    </div>

    <!-- 知识薄弱点 -->
    <div v-if="parsed.weakPoints.length" class="report-section">
      <div class="section-title">
        <span class="dot dot-weak"></span>知识薄弱点
      </div>
      <ul class="point-list weak">
        <li v-for="(p, i) in parsed.weakPoints" :key="i">{{ p }}</li>
      </ul>
    </div>

    <!-- 改进建议 -->
    <div v-if="parsed.improvements.length" class="report-section">
      <div class="section-title">
        <span class="dot dot-improve"></span>改进建议
      </div>
      <ul class="point-list improve">
        <li v-for="(p, i) in parsed.improvements" :key="i">{{ p }}</li>
      </ul>
    </div>

    <div class="report-foot">
      <el-button size="small" @click="$emit('download')">下载总结报告 (.md)</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  report: { type: String, default: '' },
  reportData: { type: Object, default: null },
})
defineEmits(['download'])

const RADIUS = 52
const circumference = 2 * Math.PI * RADIUS

function clamp(n) {
  if (Number.isNaN(n)) return null
  return Math.max(0, Math.min(100, n))
}

const parsed = computed(() => {
  const d = props.reportData
  // 后端已产出结构化数据时优先使用（避免前端重复解析 markdown）
  if (d && (d.score != null || d.dimensions || d.weak_points || d.improvements)) {
    return {
      raw: false,
      score: d.score,
      dimensions: (d.dimensions || []).map((x) => ({
        label: x.label,
        score: clamp(parseInt(x.score, 10)),
      })),
      weakPoints: d.weak_points || [],
      improvements: d.improvements || [],
      strengths: [],
    }
  }
  // 无结构化数据：仅展示原文，前端不再复制一份解析正则（AGENTS 纪律，bug #29）
  return { raw: true, score: null, dimensions: [], weakPoints: [], improvements: [] }
})
const ringOffset = computed(() => {
  if (parsed.value.score == null) return 0
  return circumference * (1 - parsed.value.score / 100)
})

function dimColor(score) {
  return score >= 60 ? 'linear-gradient(90deg, var(--brand), var(--brand-light))' : 'linear-gradient(90deg, #f7a84f, #ffc26e)'
}
</script>

<style scoped>
.report-panel {
  background: #fff;
  border: 1px solid #e7ecf4;
  border-radius: 16px;
  padding: 18px 20px 14px;
  margin: 14px 0 4px;
  box-shadow: 0 4px 20px rgba(var(--brand-rgb), 0.08);
}
.report-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.report-raw {
  margin-top: 14px;
  padding: 14px 16px;
  background: #f7f9fd;
  border: 1px solid #e7ecf4;
  border-radius: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.7;
  color: #3a4664;
}
.report-title-box {
  min-width: 0;
}
.report-kicker {
  font-size: 12px;
  color: var(--brand);
  letter-spacing: 1px;
  margin-bottom: 4px;
}
.report-title {
  font-size: 20px;
  font-weight: 700;
  color: #2b3448;
}
.report-sub {
  font-size: 12px;
  color: #7b879c;
  margin-top: 4px;
}
.score-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex: 0 0 auto;
}
.ring-svg {
  width: 120px;
  height: 120px;
  transform: rotate(-90deg);
}
.ring-bg {
  fill: none;
  stroke: #eef1f7;
  stroke-width: 10;
}
.ring-fg {
  fill: none;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.8s ease;
}
.score-num {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -58%);
  font-size: 30px;
  font-weight: 800;
  color: #2b3448;
}
.score-total {
  position: absolute;
  bottom: 26px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: #9aa5bb;
}
.report-section {
  margin-top: 16px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #2b3448;
  margin-bottom: 10px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.dot-dim {
  background: var(--brand);
}
.dot-weak {
  background: #f7a84f;
}
.dot-improve {
  background: #34c77b;
}
.dim-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.dim-label {
  width: 110px;
  flex: 0 0 110px;
  font-size: 13px;
  color: #56637a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dim-track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: #eef1f7;
  overflow: hidden;
}
.dim-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.7s ease;
}
.dim-score {
  width: 28px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
  color: #2b3448;
}
.point-list {
  margin: 0;
  padding: 0 0 0 2px;
  list-style: none;
}
.point-list li {
  position: relative;
  padding: 6px 0 6px 18px;
  font-size: 13px;
  line-height: 1.6;
  color: #56637a;
  border-bottom: 1px dashed #eef1f7;
}
.point-list li:last-child {
  border-bottom: none;
}
.point-list li::before {
  position: absolute;
  left: 0;
  top: 9px;
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.point-list.weak li::before {
  background: #f7a84f;
}
.point-list.improve li::before {
  background: #34c77b;
}
.report-foot {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #eef1f7;
}
</style>
