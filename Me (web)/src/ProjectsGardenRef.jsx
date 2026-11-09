import { useEffect, useMemo, useRef, useState } from 'react';
import './ProjectsGardenRef.css';

const PROJECT_ORDER = [
  'AI 追星出行规划系统',
  '2012 Escape 双关卡逃生游戏',
  '舞蹈健身自适应教学系统',
  '开源情报新闻监测系统',
  '直拍人物智能跟踪与自动构图工具',
  'Python 数据采集与可视化练习',
  'ECHO 用户反馈分析与产品改进工作台',
];
const PROJECT_MEDIA = {
  '直拍人物智能跟踪与自动构图工具': [
    { src: '/projects/fancam/fancam-select.png', alt: 'Fancam Maker 导入视频并框选人物', label: '导入与框选' },
    { src: '/projects/fancam/fancam-analysis.png', alt: 'Fancam Maker 人物跟踪分析预览', label: '跟踪与分析' },
  ],
  'AI 追星出行规划系统': [
    { src: '/projects/star-trip/planner.png', alt: 'AI 追星出行规划系统行程规划页面', label: '行程规划页面' },
  ],
  '2012 Escape 双关卡逃生游戏': [
    { src: '/projects/escape-2012/level-city.png', alt: '2012 Escape 城市地震逃生第一关', label: '城市地震关卡' },
    { src: '/projects/escape-2012/level-hawaii.png', alt: '2012 Escape 夏威夷火山第二关', label: '夏威夷火山关卡' },
    { src: '/projects/escape-2012/ending.png', alt: '2012 Escape 抵达目的地后的游戏结局', label: '游戏结局' },
  ],  '舞蹈健身自适应教学系统': [
    { src: '/projects/dance/pose-analysis.png', alt: '舞蹈健身教学姿态分析页面', label: '视频姿态分析' },
    { src: '/projects/dance/action-segments.png', alt: '舞蹈健身教学动作步骤页面', label: '动作步骤拆分' },
    { src: '/projects/dance/action-energy.png', alt: '舞蹈健身教学动作能量统计', label: '动作能量统计' },
    { src: '/projects/dance/pose-compare.png', alt: '舞蹈示范与用户摄像头姿态对比', label: '示范与摄像头对比' },
    { src: '/projects/dance/training-score.png', alt: '舞蹈健身教学当前步骤动作评分', label: '训练动作评分' },
  ],  'Python 数据采集与可视化练习': [
    { src: '/projects/python-data/salary-chart.png', alt: 'Python 岗位薪资数据城市均值柱状图', label: '岗位薪资城市均值' },
    { src: '/projects/python-data/education-chart.png', alt: 'Python 教育数据分组对比柱状图', label: '教育数据对比' },
    { src: '/projects/python-data/danmaku-chart.png', alt: 'Python B站弹幕分段数量趋势图', label: '弹幕时间分布' },
    { src: '/projects/python-data/news-data.png', alt: 'Python 采集整理的新闻标题、点击量与链接数据', label: '新闻数据采集' },
    { src: '/projects/python-data/danmaku-wordcloud.png', alt: 'Python 弹幕文本词云可视化', label: '弹幕词云' },
  ],  'ECHO 用户反馈分析与产品改进工作台': [
    { src: '/projects/echo/echo-collect.png', alt: 'ECHO 评论自动采集与分析界面', label: '评论采集' },
    { src: '/projects/echo/echo-dashboard.png', alt: 'ECHO 用户反馈分析工作台', label: '反馈工作台' },
    { src: '/projects/echo/echo-submit.png', alt: 'ECHO 用户评价提交页面', label: '评价提交' },
    { src: '/projects/echo/echo-analysis.png', alt: 'ECHO 待改进问题分析与 AI 建议页面', label: '分析与建议' },
  ],
};
const PROJECT_REPOSITORIES = {
  '2012 Escape 双关卡逃生游戏': 'https://github.com/Chenjiangxiaoyu/XIAOYU1/tree/main/2012Escape',
  '直拍人物智能跟踪与自动构图工具': 'https://github.com/Chenjiangxiaoyu/XIAOYU1/tree/main/CATCH',
  '舞蹈健身自适应教学系统': 'https://github.com/Chenjiangxiaoyu/XIAOYU1/tree/main/Dance',
  'ECHO 用户反馈分析与产品改进工作台': 'https://github.com/Chenjiangxiaoyu/XIAOYU1/tree/main/ECHO',
  'AI 追星出行规划系统': 'https://github.com/Chenjiangxiaoyu/XIAOYU1/tree/main/Star',
};
const PROJECT_MARKERS = [
  { x: 0.24, y: 0.42, color: '#f4f1eb', label: 'AI 出行' },
  { x: 0.36, y: 0.76, color: '#f5f2eb', label: 'Escape' },
  { x: 0.49, y: 0.42, color: '#f5f2eb', label: '舞蹈健身' },
  { x: 0.61, y: 0.76, color: '#ece4d7', label: '情报监测' },
  { x: 0.74, y: 0.42, color: '#f5f2eb', label: '智能跟踪' },
  { x: 0.85, y: 0.76, color: '#f5f2eb', label: '数据可视化' },
  { x: 0.93, y: 0.42, color: '#edf1ed', label: 'ECHO' },
];
const DRIFT_BOATS = [
  { x: 0.16, y: 0.45, phase: 0.35, color: '#f7f5f1', scale: 0.82 },
  { x: 0.31, y: 0.63, phase: 0.72, color: '#f7f5f1', scale: 0.76 },
  { x: 0.44, y: 0.47, phase: 0.48, color: '#f7f5f1', scale: 0.92 },
  { x: 0.67, y: 0.66, phase: 0.18, color: '#f7f5f1', scale: 0.78 },
  { x: 0.78, y: 0.45, phase: 0.6, color: '#f7f5f1', scale: 0.84 },
  { x: 0.93, y: 0.57, phase: 0.42, color: '#f7f5f1', scale: 0.72 },
];

function PaperBoat({ color = '#f7f5f1' }) {
  return <svg className="paper-boat" viewBox="0 0 150 86" aria-hidden="true">
    <path d="M18 54 L132 54 L105 75 Q76 81 45 73 Z" fill={color} stroke="#777773" strokeWidth="1.8" strokeLinejoin="round" />
    <path d="M24 53 L74 58 L48 70 Z" fill="#fff" stroke="#99958c" strokeWidth="1" />
    <path d="M74 58 L127 54 L105 73 Z" fill={color} stroke="#99958c" strokeWidth="1" />
    <path d="M32 58 Q70 65 114 58" fill="none" stroke="#fff" strokeOpacity=".78" strokeWidth="1.2" />
  </svg>;
}

function FloatingProjectSign({ color, label }) {
  return <svg className="floating-sign" viewBox="0 0 170 150" aria-hidden="true">
    <ellipse cx="86" cy="137" rx="55" ry="7" fill="#8b8984" opacity=".16" />
    <path d="M23 118 Q86 108 149 118 L130 139 Q86 149 42 139 Z" fill="#c9c7c2" stroke="#777570" strokeWidth="2" strokeLinejoin="round" />
    <path d="M86 119 L86 75" fill="none" stroke="#777570" strokeWidth="3" />
    <path d="M26 35 Q84 29 145 35 L142 77 Q84 83 28 77 Z" fill={color} stroke="#66645f" strokeWidth="2.2" strokeLinejoin="round" />
    <path d="M32 42 Q83 38 139 41 M33 72 Q87 76 138 71" fill="none" stroke="#aaa69e" strokeWidth="1.2" />
    <circle cx="35" cy="39" r="2" fill="#8e8980" /><circle cx="136" cy="39" r="2" fill="#8e8980" />
    <text x="85" y="59" textAnchor="middle" dominantBaseline="middle" fill="#514f4a" fontSize={label.length > 5 ? 11 : 13} fontFamily="Microsoft YaHei, sans-serif" fontWeight="600">{label}</text>
  </svg>;
}

function PierAndRiver() {
  return <>
    <div className="pier-sky" aria-hidden="true">
      <svg className="sky-clouds" viewBox="0 0 1600 430" preserveAspectRatio="none">
        <g className="sketch-cloud sketch-cloud--left"><path d="M70 135 Q56 105 91 91 Q103 52 150 68 Q175 19 230 52 Q273 23 306 67 Q353 51 366 91 Q414 94 404 133 Q382 162 324 153 Q262 170 217 153 Q146 169 111 151 Q82 157 70 135Z" /><path d="M82 139 Q118 166 161 151 Q226 170 274 151 Q346 164 393 137" /></g>
        <g className="sketch-cloud sketch-cloud--middle"><path d="M490 111 Q477 87 510 75 Q523 41 566 55 Q594 15 632 50 Q677 33 698 67 Q744 58 755 90 Q794 96 780 126 Q756 147 712 138 Q649 152 615 137 Q557 153 524 136 Q497 140 490 111Z" /></g>
        <g className="sketch-cloud sketch-cloud--right"><path d="M1060 127 Q1046 99 1078 86 Q1096 46 1138 64 Q1170 16 1212 59 Q1256 26 1287 69 Q1337 57 1354 93 Q1395 95 1382 128 Q1360 153 1310 143 Q1257 160 1214 143 Q1151 156 1117 140 Q1077 149 1060 127Z" /><path d="M1073 130 Q1112 151 1153 139 Q1205 156 1247 140 Q1310 155 1372 132" /></g>
        <g className="sketch-cloud sketch-cloud--small"><path d="M850 182 Q842 164 862 157 Q870 135 895 143 Q914 119 934 143 Q958 132 970 151 Q998 148 1003 168 Q1025 172 1016 190 Q1003 203 975 198 Q938 208 913 197 Q880 206 867 195 Q853 199 850 182Z" /></g>
      </svg>
      <svg className="lighthouse" viewBox="0 0 150 230" aria-hidden="true">
        <path d="M17 214 Q45 187 67 193 Q91 179 130 214 L115 227 L28 227Z" fill="#e9e8e5" stroke="#777570" strokeWidth="2" />
        <path d="M51 193 L62 57 L88 57 L100 193Z" fill="#f7f6f3" stroke="#66645f" strokeWidth="2.3" />
        <path d="M56 145 L96 145 M58 111 L93 111 M60 80 L90 80" stroke="#99968f" strokeWidth="2" />
        <path d="M58 58 L58 44 L92 44 L92 58 M54 44 L96 44 L88 32 L63 32Z" fill="#f0efeb" stroke="#66645f" strokeWidth="2" />
        <path d="M68 32 L68 17 L82 17 L82 32 M66 17 L84 17 L75 8Z" fill="#f0efeb" stroke="#66645f" strokeWidth="2" />
        <path d="M43 195 Q75 188 108 195" fill="none" stroke="#aaa79f" strokeWidth="1.4" />
        <rect x="69" y="161" width="13" height="24" rx="6" fill="#deddd9" stroke="#88857e" strokeWidth="1.3" />
      </svg>
      <div className="pier-title"><span>项目经历</span></div>
    </div>
    <div className="horizon-line" aria-hidden="true" />
    <div className="pier-river" aria-hidden="true">
      <svg className="river-etching river-etching--far" viewBox="0 0 1600 700" preserveAspectRatio="none"><defs><pattern id="river-pencil" width="120" height="38" patternUnits="userSpaceOnUse"><path d="M-8 10 Q9 2 27 10 T63 10 T99 10 T135 10 M-17 27 Q4 19 24 27 T65 27 T106 27 T147 27" fill="none" stroke="#aaa8a3" strokeWidth="1.2" opacity=".52" /></pattern></defs><rect width="1600" height="700" fill="url(#river-pencil)" /></svg>
      <svg className="river-etching river-etching--near" viewBox="0 0 1600 700" preserveAspectRatio="none"><path d="M-40 370 Q20 335 82 370 T205 370 T328 370 T451 370 T574 370 T697 370 T820 370 T943 370 T1066 370 T1189 370 T1312 370 T1435 370 T1558 370 T1681 370" /><path d="M-40 468 Q20 429 82 468 T205 468 T328 468 T451 468 T574 468 T697 468 T820 468 T943 468 T1066 468 T1189 468 T1312 468 T1435 468 T1558 468 T1681 468" /><path d="M-40 581 Q20 546 82 581 T205 581 T328 581 T451 581 T574 581 T697 581 T820 581 T943 581 T1066 581 T1189 581 T1312 581 T1435 581 T1558 581 T1681 581" /></svg>
      <div className="river-glints" />
    </div>
    <svg className="pier-deck" viewBox="0 0 1200 900" preserveAspectRatio="none" aria-hidden="true">
      <path className="pier-deck-shadow" d="M455 748 L745 748 L815 900 L385 900 Z" />
      <g className="pier-wood-boards">
        <path d="M455 748 L503.3 748 L456.7 900 L385 900 Z" />
        <path d="M503.3 748 L551.7 748 L528.3 900 L456.7 900 Z" />
        <path d="M551.7 748 L600 748 L600 900 L528.3 900 Z" />
        <path d="M600 748 L648.3 748 L671.7 900 L600 900 Z" />
        <path d="M648.3 748 L696.7 748 L743.3 900 L671.7 900 Z" />
        <path d="M696.7 748 L745 748 L815 900 L743.3 900 Z" />
      </g>
      <path className="pier-deck-face" d="M455 748 L745 748 L815 900 L385 900 Z" />
      <path className="pier-deck-edge" d="M455 748 L745 748 L815 900 L385 900 Z" />
      <path className="pier-plank" d="M437 788 Q600 793 763 788" /><path className="pier-plank" d="M418 832 Q600 841 782 832" />
      <path className="pier-grain" d="M477 759 Q467 801 451 827 M492 851 Q485 872 476 887 M565 761 Q558 796 556 815 M635 848 Q643 868 646 888" />
      <path className="pier-grain" d="M726 759 Q736 800 751 827 M710 851 Q718 873 726 887 M600 761 Q603 794 606 813 M540 849 Q536 872 534 887" />
      <g className="pier-nails"><circle cx="468" cy="781" r="1.5"/><circle cx="732" cy="781" r="1.5"/><circle cx="442" cy="824" r="1.6"/><circle cx="758" cy="824" r="1.6"/><circle cx="410" cy="870" r="1.7"/><circle cx="790" cy="870" r="1.7"/></g>
    </svg>
    <div className="far-paper-boat" aria-hidden="true"><PaperBoat color="#efeeeb" /></div>
  </>;
}

function ProjectCardDeck({ project, onClose }) {
  const [activeCard, setActiveCard] = useState(2);
  const [expandedMedia, setExpandedMedia] = useState(null);
  const media = PROJECT_MEDIA[project.heading] || [];
  useEffect(() => {
    if (!expandedMedia) return undefined;
    const closeOnEscape = (event) => { if (event.key === 'Escape') setExpandedMedia(null); };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [expandedMedia]);
  const cards = [
    { letter: 'S', title: 'Situation · 情境', text: project.situation || '项目背景与要解决的问题待补充。' },
    { letter: 'T', title: 'Task · 任务', text: project.task || '项目目标与本人承担的职责待补充。' },
    { letter: 'A', title: 'Action · 行动', text: project.action || '具体行动待补充。', techStack: project.techStack },
    { letter: 'R', title: 'Result · 结果', text: project.result || '项目成果与实际影响待补充。', href: PROJECT_REPOSITORIES[project.heading] },
  ];
  return <div className={"project-deck-anchor" + (media.length > 4 ? " project-deck-anchor--many" : "")} onClick={onClose}>
    <button type="button" className="project-star-close" onClick={onClose} aria-label="关闭 STAR 卡片">×</button>
    {media.length > 0 && <div className={"project-media-float" + (media.length > 2 ? " project-media-float--multi" : "") + (media.length > 4 ? " project-media-float--many" : "")} aria-label={project.heading + " 项目界面截图"}>
      {media.map((image, index) => <button type="button" key={image.src} className={"project-media-float__item project-media-float__item--" + (index % 2 ? "analysis" : "select")} style={{ "--media-order": index }} onClick={(event) => { event.stopPropagation(); setExpandedMedia(image); }} aria-label={"放大查看：" + image.label}>
        <img src={image.src} alt={image.alt} /><span className="project-media-float__caption">{image.label}</span>
      </button>)}
    </div>}
    <div className="project-card-stack" onClick={(event) => event.stopPropagation()} aria-label={`${project.heading} 项目 STAR 卡片`}>
      {cards.map((card, index) => <article key={card.letter} className={`project-star-card project-star-card--${card.letter.toLowerCase()}${activeCard === index ? ' project-star-card--active' : ''}`} style={{ '--fan-index': index }} onClick={() => setActiveCard(index)}>
        <span className="project-star-letter">{card.letter}</span>
        <span className="project-star-eyebrow">{card.href ? <a href={card.href} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>{card.title}</a> : card.title}</span>
        <h2>{project.heading}</h2>
        {project.meta && <div className="project-star-meta">{project.meta}</div>}
        <p>{card.text}</p>
        {card.techStack && <div className="project-card-tags">技术栈：{card.techStack}</div>}
      </article>)}
    </div>
    {expandedMedia && <div className="project-media-lightbox" role="dialog" aria-modal="true" aria-label={expandedMedia.label} onClick={(event) => { event.stopPropagation(); setExpandedMedia(null); }}>
      <button type="button" className="project-media-lightbox__close" onClick={(event) => { event.stopPropagation(); setExpandedMedia(null); }} aria-label="关闭图片">×</button>
      <figure className="project-media-lightbox__figure" onClick={(event) => event.stopPropagation()}><img src={expandedMedia.src} alt={expandedMedia.alt} /><figcaption>{expandedMedia.label}</figcaption></figure>
    </div>}
  </div>;
}

export default function ProjectsGardenRef({ room, onClose }) {
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedBoatId, setSelectedBoatId] = useState(null);
  const boatRefs = useRef({});
  const projects = useMemo(() => {
    const byName = new Map((room.items || []).map((item) => [item.heading, item]));
    return PROJECT_ORDER.map((name) => byName.get(name)).filter(Boolean);
  }, [room.items]);

  const openBoat = (event, project, id) => {
    event.stopPropagation(); setSelectedProject(project); setSelectedBoatId(id);
  };
  const closeDeck = () => { setSelectedProject(null); setSelectedBoatId(null); };

  return <section className="projects-garden-ref" aria-label="项目经历码头">
    <PierAndRiver />
    <div className="river-boats" aria-label="河上的纸船">
      {projects.map((project, index) => {
        const boat = PROJECT_MARKERS[index] || PROJECT_MARKERS[0]; const id = `project-boat-${index}`;
        const duration = 65;
        return <button key={project.heading} ref={(node) => { boatRefs.current[id] = node; }} type="button" className={`river-boat river-boat--project${selectedBoatId === id ? ' river-boat--selected' : ''}`}
          style={{ '--boat-y': `${boat.y * 100}%`, '--boat-delay': `${-index * duration / projects.length}s`, '--boat-color': boat.color, '--boat-duration': `${duration}s`, animationPlayState: selectedBoatId === id ? 'paused' : 'running' }}
          onClick={(event) => openBoat(event, project, id)} aria-label={`查看项目：${project.heading}`}><FloatingProjectSign color={boat.color} label={boat.label} /></button>;
      })}
      {DRIFT_BOATS.map((boat, index) => { const duration = 50 + index * 4.4; return <div key={`drift-${index}`} className="river-boat river-boat--drift" style={{ '--boat-y': `${boat.y * 100}%`, '--boat-delay': `${-boat.phase * duration}s`, '--boat-color': boat.color, '--boat-duration': `${duration}s`, '--boat-scale': 1 }}><PaperBoat color={boat.color} /></div>; })}
    </div>
    <header className="garden-ref-header"><button type="button" className="garden-ref-back" onClick={onClose}>← 回到走廊</button><span className="garden-ref-hint">纸船顺着水波，从左向右漂流</span></header>
    {selectedProject && <ProjectCardDeck project={selectedProject} onClose={closeDeck} />}
  </section>;
}





