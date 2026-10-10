/* ============================================================
   GHOST — Personal Archive · 站点内容数据（集中管理）
   说明：当前全部为【占位内容】，等待替换为真实作品/文章/链接。
   封面图由 AI 图像接口按 prompt 生成，仅作视觉占位。
   ============================================================ */

// 封面图生成地址（统一构造，替换素材时只改这里）
function cover(prompt, size) {
  return 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=' +
    encodeURIComponent(prompt) + '&image_size=' + (size || 'landscape_4_3');
}

window.SITE_DATA = {

  /* ---------- 导航 ---------- */
  nav: [
    { label: '首页', href: '#top' },
    { label: '作品', href: '#works' },
    { label: '随笔', href: '#notes' },
    { label: '关于', href: '#about' }
  ],

  /* ---------- 精选作品（占位，手动精选；未发布内容不得出现在这里） ---------- */
  works: [
    {
      title: '潮汐词典（占位标题）',
      category: 'AI 项目',
      date: '2026.09',
      aspect: '4-3',
      href: '#',
      placeholder: true,
      coverPrompt: 'Experimental AI generative art, thousands of fine vermilion red lines forming a wave of letters on deep indigo blue, risograph screen print texture, minimal, high detail',
      summary: '一个让语言模型每天生成一个生僻词、再用图像重新解释它的实验项目。关注语词与视觉之间的错位，目前记录到第 27 天。',
      tags: ['LLM', '生成图像', '每日实验']
    },
    {
      title: '夜航 · 未命名短片（占位标题）',
      category: '视频创作',
      date: '2026.08',
      aspect: '16-10',
      href: '#',
      placeholder: true,
      reverse: true,
      coverPrompt: 'Indie short film cinematic still, lone figure walking a quiet street at night, neon reflections on wet road, muted teal and burnt orange, subtle film grain, quiet atmosphere',
      summary: '十分钟手机短片习作：一次没有目的地的夜间行走。粗剪已完成，正在处理声音与字幕，预计年底重剪一版。',
      tags: ['手机拍摄', '粗剪', '声音设计']
    },
    {
      title: 'GHOST 视觉识别 · 草稿集（占位标题）',
      category: '设计',
      date: '2026.07',
      aspect: '4-3',
      href: '#',
      placeholder: true,
      offset: true,
      coverPrompt: 'Graphic design posters pinned on a white studio wall, bold red and deep blue screen printed typography, folded paper texture, swiss poster design, natural light',
      summary: '为本站整理的海报式视觉规范：纯色、红橙潮水、克制排版。这里保留被放弃的 G 标志草稿与潮水素材的演化过程。',
      tags: ['视觉识别', '海报', '丝网印刷感']
    },
    {
      title: 'Tide Canvas（占位标题）',
      category: '开发实验',
      date: '2026.06',
      aspect: '16-10',
      href: '#',
      placeholder: true,
      reverse: true,
      coverPrompt: 'Creative coding workspace, laptop screen showing generative red wave particle art on deep blue, open notebook with sketches, soft daylight, photographic',
      summary: '用 Canvas 复刻手绘潮水的小型练习：对比 SVG 位移滤镜、帧动画与物理流体三种方案，最终选择了最“印刷感”的一种。',
      tags: ['Canvas', 'SVG', '动效']
    }
  ],

  /* ---------- 最近随笔（占位，默认展示 5 篇） ---------- */
  notes: [
    {
      title: '把一个 Agent 拆成小工具之后',
      category: 'AI 技术',
      date: '2026-09-15',
      href: '#',
      placeholder: true,
      summary: '单体提示词越写越长，不如拆成可组合的工具：一次重构后，调试方式和可复用性都变了。'
    },
    {
      title: '学 Transformer 时卡住的三个问题',
      category: '学习记录',
      date: '2026-09-02',
      href: '#',
      placeholder: true,
      summary: '注意力为什么除以 √d、位置信息到底加在了哪里、训练和推理形状为什么不一样。'
    },
    {
      title: '为什么想做这个网站',
      category: '创作日志',
      date: '2026-08-24',
      href: '#',
      placeholder: true,
      summary: '不是为了展示成品，而是给那些还没成形的念头一个存放处——关于克制、实验和长期记录。'
    },
    {
      title: '关于“还没想明白的事”',
      category: '个人思考',
      date: '2026-08-11',
      href: '#',
      placeholder: true,
      summary: '半成品是否值得公开？半匿名身份如何成立？暂时没有答案，但先把问题写下来。'
    },
    {
      title: '用提示词管理一个项目的一次实验',
      category: 'AI 技术',
      date: '2026-07-30',
      href: '#',
      placeholder: true,
      summary: '把需求、规范、验收清单全部写成交接文档，让另一个 Agent 接手——结论与踩坑记录。'
    }
  ],

  /* ---------- About（占位，3–5 行核心介绍） ---------- */
  about: {
    lead: 'GHOST 是一个半匿名的创作身份。',
    paragraphs: [
      '我做 AI 相关的小实验，也写代码、剪视频、做设计，把过程中产生的东西留在这里。',
      '这个站点收藏完成的作品，也收藏尚未成形的念头——后者同样值得被记录。',
      '更多介绍将在独立的关于页展开；此处保持克制。'
    ],
    interests: ['AI 与工具', '生成式视觉', '视频叙事', '前端与创意编码', '阅读笔记']
  },

  /* ---------- 社交链接（占位，待替换为真实公开链接） ---------- */
  social: [
    { label: 'GitHub', href: '#', placeholder: true },
    { label: 'X / Twitter', href: '#', placeholder: true },
    { label: 'Email', href: '#', placeholder: true }
  ],

  /* ---------- 页脚 ---------- */
  footer: {
    closing: '做点东西，记下所想。',
    note: '所有作品与文章均为占位内容，将逐步替换为真实记录。'
  }
};
