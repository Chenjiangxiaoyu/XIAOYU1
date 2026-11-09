import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import GreetingAvatar from './components/canvas/GreetingAvatar.jsx';
import * as THREE from 'three';
import gsap from 'gsap';
import ProjectsGarden from './ProjectsGardenRef.jsx';
import SkillsRoom from './SkillsRoom.jsx';
import UnlockRealRoom from './UnlockRealRoom.jsx';
import './App.css';

const rooms = [
  {
    id: 'intent', label: '求职意向', title: '想做更贴近用户的产品', icon: '意',
    body: '意向岗位：产品实习生', facts: ['意向城市：北京', '求职类型：实习', '当前状态：月内到岗', '可实习：5天/周，3个月+'], color: '#d4a76a', side: 1, z: -10.1,
  },
  {
    id: 'education', label: '教育经历', title: '大连理工大学', icon: '学',
    body: '2025.09 — 至今 · 本科', facts: ['学院：软件学院', '专业：智能无人系统技术', '主修：程序设计、智能硬件设计、数据结构与算法、人工智能基础、数字逻辑系统', '自学：Excel 函数、Python'], color: '#8ca99a', side: -1, z: -14.5,
  },
  {
    id: 'projects', label: '作品集', title: '把想法做成能体验的原型', icon: '作', color: '#b18f9b', side: -1, z: -5.7,
    items: [
      {
        heading: '舞蹈健身自适应教学系统', meta: '大学生创新项目 · 项目组长',
        situation: '• 舞蹈学习需要在参考视频、动作拆解、摄像头跟练与训练反馈之间衔接。\n• 视频主体不清、跟练节奏不合适等问题，会影响用户理解动作和持续练习。',
        task: '• 作为项目组长，负责需求梳理、交互方案设计，并使用 AI 工具辅助原型开发。\n• 规划从视频分析到训练记录的核心流程，并探索适应不同动作节奏的教学方式。',
        action: '• 参与搭建“视频分析—分步教学—摄像头跟练—评分反馈—训练记录”原型流程。\n• 提出手动选择参考视频主体、视频与摄像头分屏及教学模式切换；推动快速动作区间加密采样。',
        result: '• 形成覆盖教学、跟练和反馈环节的产品原型流程，并将关键需求转化为交互方案。\n• 针对快速动作跟不上的问题提出采样优化方向，为后续改进跟练节奏与提示提供依据。',
        techStack: 'Vue 3、TypeScript、MediaPipe、Three.js、Codex',
      },
      {
        heading: '开源情报新闻监测系统', meta: '导师项目',
        situation: '• 原有系统已具备新闻监测功能，但新闻回看和重点内容保存不够方便。\n• 新闻摘要与倾向信息缺少直观入口，用户需要在浏览和整理信息之间反复切换。',
        task: '• 基于导师已有系统迭代页面与功能，完善新闻浏览和信息管理体验。\n• 补充历史、收藏、摘要和倾向展示功能，并与原有页面流程衔接。',
        action: '• 新增浏览历史与收藏管理，支持回看、删除和清空，并使用 localStorage 保存。\n• 新增新闻摘要弹窗，抓取文章正文后调用百度智能云新闻摘要 API；基于标题关键词规则识别倾向，并用 ECharts 展示分布。',
        result: '• 在原有系统中补充历史管理、收藏、摘要和倾向分布功能，完善新闻浏览与整理流程。\n• 明确区分了 API 摘要和关键词规则判断的用途，避免将规则识别描述为情感分析 API。',
        techStack: 'PHP、JavaScript、JSON、ECharts、百度智能云新闻摘要 API',
      },
      {
        heading: '2012 Escape 双关卡逃生游戏', meta: '玩法与关卡设计 · AI 辅助开发',
        situation: '• 项目希望以城市地震和夏威夷火山为主题，制作双关卡逃生游戏。\n• 需要将不同场景转化为连续的闯关体验，并通过障碍和状态反馈推动游戏进程。',
        task: '• 负责玩法与关卡设计，并参与 AI 辅助开发和工程问题排查。\n• 规划两关流程，串联开始、闯关、受伤、失败重开、关卡切换与结局。',
        action: '• 设计城市地震、夏威夷火山两种关卡场景及对应的闯关流程。\n• 参与实现动态落石与岩浆球、生命值反馈、角色动画和多层视差滚动。',
        result: '• 完成包含双场景和主要闯关流程的游戏原型，覆盖开始、失败重开、关卡切换与结局。\n• 实现动态障碍、生命值反馈和场景动画等内容，积累了玩法拆解与功能协作经验。',
        techStack: 'C++17、EasyX、Visual Studio、ChatGPT/Codex',
      },
      {
        heading: '直拍人物智能跟踪与自动构图工具', meta: '需求梳理与跟踪逻辑迭代',
        situation: '• 直拍人物时容易出现跟踪框丢失、快速动作下画面滞后或构图不稳等问题。\n• 单一跟踪结果难以适应不同动作状态，需要结合其他视觉信息辅助校验。',
        task: '• 负责梳理人物跟踪与画面稳定相关需求，并参与交互方案和跟踪逻辑调试。\n• 重点探索跟踪框校验、人物偏移纠正和快速运动场景下的构图优化。',
        action: '• 参与结合 MediaPipe 姿态关键点与人体分割结果，校验 OpenCV CSRT 跟踪框。\n• 针对人物偏移和快速运动场景，参与位置纠偏、光流辅助分析与构图平滑方案调试。',
        result: '• 形成结合姿态、人体分割与目标跟踪结果进行校验的实现思路。\n• 针对快速动作和构图不稳提出辅助分析与平滑方案，积累了多种视觉信息协同使用的经验。',
        techStack: 'Python、OpenCV（CSRT、Farneback 光流）、MediaPipe Pose',
      },
      {
        heading: 'AI 追星出行规划系统', meta: '产品方案 · 全栈原型',
        situation: '• 粉丝跨城观看演出时，需要分别查询演出、交通和住宿信息，再自行拼接行程。\n• 信息分散且日期关联复杂，项目希望通过网页集中收集条件并生成行程建议。',
        task: '• 负责产品方案与全栈原型开发，设计城市、演出日期、偏好和预算等输入。\n• 探索整合演出、交通、住宿数据，并调用 AI API 生成与演出日期相关的行程建议。',
        action: '• 搭建出行规划网页原型，编写数据采集模块，尝试整合大麦演出、12306 火车、携程航班和美团酒店信息。\n• 根据演出日期推算住宿与返程日期，将整理后的信息传入 DeepSeek API，并完成域名配置和部署尝试。',
        result: '• 完成从条件输入、信息采集与整理到 AI 行程建议展示的原型流程，并尝试配置域名和部署。\n• 受数据采集稳定性及上线审批等因素影响，项目未正式上线，也识别出数据来源对产品可用性的影响。',
        techStack: 'Python、FastAPI、Requests、Selenium、HTML/CSS/JavaScript、DeepSeek API',
      },
      {
        heading: 'Python 数据采集与可视化练习', meta: '个人练习',
        situation: '• 招聘岗位、景点和酒店等公开信息分散在不同页面，难以直接汇总比较。\n• B 站弹幕等内容需要进一步解析，才能观察其时间分布和变化趋势。',
        task: '• 通过个人练习熟悉 Python 数据采集、字段解析、清洗整理和基础可视化流程。\n• 围绕岗位薪资、公开地点信息和弹幕时间分布完成数据获取、整理与分析。',
        action: '• 使用 Requests、BeautifulSoup、lxml 和 Selenium 采集公开信息，完成字段解析、格式整理与 Excel 导出。\n• 使用 pandas 清洗岗位薪资并按城市汇总，借助 Pyecharts 绘图；解析 B 站弹幕时间并统计分段趋势。',
        result: '• 完成招聘、景点和酒店信息整理，以及岗位薪资城市汇总和 B 站弹幕趋势分析。\n• 积累了从公开数据采集、字段清洗到统计与图表呈现的实践经验。',
        techStack: 'Python、Requests、BeautifulSoup、lxml、Selenium、pandas、Pyecharts',
      },
      {
        heading: 'ECHO 用户反馈分析与产品改进工作台', meta: '2026.11–至今 · 产品方案与 AI 原型开发',
        situation: '• 产品团队需要从分散的用户评价中提炼体验问题与改进机会，为产品决策提供依据。\n• 原型已呈现反馈录入、发现查看和 AI 追问流程，但真实评论的批量采集、持续分析和效果评测能力仍需补齐。',
        task: '• 在现有工作台上搭建评论处理闭环，接入评论数据源，完成批量采集、清洗、去重、持久化和逐条分析。\n• 建立独立评测流程，让模型输出能够按样本复核、留档和量化。',
        action: '• 设计爬虫接口配置和分页采集流程，支持字段映射、断点续接、重复数据去重，以及失败后的继续处理。\n• 使用 SQLite 保存评论与任务状态；清洗文本并脱敏隐私信息，保留原始数据与清洗文本的关联。\n• 复用 DeepSeek 分析流程，逐条提取情绪、价值或问题、原文证据、建议、验证方向、风险和成功标准；校验引文并将发现关联回原始评论。\n• 新建独立评测模块，支持冻结数据集、版本留档、逐次请求与 token 用量记录、人工复核、指标计算和报告导出；评测样本与日常反馈数据分开保存。\n• 技术栈：HTML、CSS、JavaScript、Python、SQLite、DeepSeek API。',
        result: '• 完成端到端处理链路与评测工具原型，通过 24 项自动化测试，覆盖分页、去重、失败重试、引用校验、评分口径和版本比较等场景。\n• 使用 11 条鸿蒙 6 相关评论进行真实模型 V0 试跑：11 条均完成结构化返回，生成 16 条待改进发现；样本量较小且金标尚待人工确认，因此不将该结果表述为准确率或正式验收通过。\n• 产出逐条可追溯的模型结果、评测报告和人工复核页面，为后续扩充数据集、裁决标注并比较模型版本建立基础。',
      },
    ],
  },
  {
    id: 'campus', label: '在校经历', title: '在团队里做好每一件小事', icon: '校', color: '#899db7', side: 1, z: -18.9,
    items: [
      { heading: '“芯聚辽沈，智联理工”寒假社会实践', meta: '宣传 · 2026.01 — 2026.03', text: '整理资料、撰写文案与视频旁白、制作汇报 PPT，团队获校三等奖。' },
      { heading: '书院文化小组、学院体育部', meta: '干事 · 2025.09 — 至今', text: '参与校园活动组织、宣传与拍摄，汇总文体积分并协助统计体测成绩。' },
    ],
  },
  {
    id: 'skills', label: '相关技能', title: '愿意快速学，也能动手做', icon: '技', color: '#d0a36f', side: -1, z: -23.3,
    items: [
      { heading: '编程基础', tags: 'C · C++ · Python' },
      { heading: '产品与交互', text: '需求拆解、交互设计、产品原型迭代、团队协作。' },
      { heading: 'AI 与开发工具', tags: 'ChatGPT · Grok · Perplexity · Codex · GitHub' },
      { heading: '设计与办公', tags: 'Meshy · ZOOOP · Excel · WPS' },
    ],
  },
  {
    id: 'profile', label: '个人评价与荣誉证书', title: '点子多，行动也快', icon: '荣', color: '#9b91ad', side: 1, z: -27.7,
    body: '善于把想法转化为产品原型；学习新工具快，交互设计与需求拆解能力强。',
    facts: ['大学英语六级', '驾驶证', '“芯聚辽沈，智联理工”社会实践校三等奖'],
  },
  { id: 'unlock-real', label: '解锁真人', title: '3D人物原型与运动日常', icon: '真', color: '#aaa7a0', side: -1, z: -32.1 },
];

function DoorSign({ label }) {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 900;
    canvas.height = 500;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#f7f6f1';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#777774';
    ctx.lineWidth = 5;
    ctx.strokeRect(18, 18, canvas.width - 36, canvas.height - 36);
    ctx.strokeStyle = 'rgba(115,115,111,.23)';
    ctx.lineWidth = 2;
    ctx.strokeRect(30, 30, canvas.width - 60, canvas.height - 60);
    ctx.strokeStyle = 'rgba(145,137,120,.2)';
    ctx.lineWidth = 2.5;
    [64, 432].forEach((y) => {
      ctx.beginPath(); ctx.moveTo(48, y); ctx.bezierCurveTo(205, y - 5, 255, y + 6, 380, y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(540, y + 3); ctx.bezierCurveTo(650, y - 4, 730, y + 5, 852, y - 1); ctx.stroke();
    });
    ctx.fillStyle = '#494741';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    let size = 112;
    ctx.font = `700 ${size}px "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`;
    while (ctx.measureText(label).width > 720 && size > 42) {
      size -= 4;
      ctx.font = `700 ${size}px "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`;
    }
    ctx.fillText(label, canvas.width / 2, canvas.height / 2 + 2);
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    map.anisotropy = 4;
    return map;
  }, [label]);

  useEffect(() => () => texture.dispose(), [texture]);
  return <group position={[0, -0.52, 0.025]}>
    <mesh><boxGeometry args={[0.7, 0.44, 0.05]} /><meshStandardMaterial color="#85837d" roughness={1} /></mesh>
    <mesh position={[0, 0, 0.028]}><boxGeometry args={[0.66, 0.4, 0.014]} /><meshStandardMaterial color="#f7f6f1" roughness={1} /></mesh>
    <mesh position={[0, 0, 0.036]}><planeGeometry args={[0.64, 0.38]} /><meshBasicMaterial map={texture} toneMapped={false} /></mesh>
    {[-0.29, 0.29].flatMap((x) => [-0.17, 0.17].map((y) => <mesh key={`${x}-${y}`} position={[x, y, 0.047]}><sphereGeometry args={[0.009, 8, 8]} /><meshStandardMaterial color="#77756f" /></mesh>))}
  </group>;
}

function SketchCloud({ position, scale = 1, rotation = 0 }) {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 360;
    canvas.height = 170;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(255,255,255,0.54)';
    ctx.strokeStyle = 'rgba(95,98,101,0.46)';
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(26, 124);
    ctx.bezierCurveTo(5, 115, 11, 82, 43, 78);
    ctx.bezierCurveTo(42, 47, 77, 36, 98, 56);
    ctx.bezierCurveTo(112, 12, 173, 15, 187, 61);
    ctx.bezierCurveTo(220, 37, 263, 54, 263, 85);
    ctx.bezierCurveTo(313, 74, 344, 104, 324, 128);
    ctx.bezierCurveTo(286, 153, 75, 148, 26, 124);
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(40, 120);
    ctx.bezierCurveTo(93, 139, 251, 140, 312, 120);
    ctx.strokeStyle = 'rgba(130,132,133,0.24)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    return map;
  }, []);
  useEffect(() => () => texture.dispose(), [texture]);
  return <mesh position={position} scale={[scale, scale, 1]} rotation={[0, rotation, 0]}>
    <planeGeometry args={[2.2, 1]} />
    <meshBasicMaterial map={texture} transparent depthWrite={false} side={THREE.DoubleSide} />
  </mesh>;
}

function FloatingIntroCloud({ visible, started, onStart }) {
  const cloudRef = useRef(null);
  const outlineRef = useRef(null);
  const textRef = useRef(null);
  const outlineTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1240;
    canvas.height = 560;
    const ctx = canvas.getContext('2d');
    const drawCloud = () => {
      ctx.beginPath();
      ctx.moveTo(178, 456);
      ctx.bezierCurveTo(88, 458, 42, 407, 68, 343);
      ctx.bezierCurveTo(12, 295, 43, 212, 116, 194);
      ctx.bezierCurveTo(104, 114, 202, 64, 282, 105);
      ctx.bezierCurveTo(330, 29, 448, 39, 493, 112);
      ctx.bezierCurveTo(555, 39, 672, 48, 718, 120);
      ctx.bezierCurveTo(788, 55, 905, 78, 922, 157);
      ctx.bezierCurveTo(1015, 106, 1114, 156, 1108, 229);
      ctx.bezierCurveTo(1190, 231, 1228, 298, 1189, 359);
      ctx.bezierCurveTo(1178, 421, 1112, 464, 1030, 448);
      ctx.bezierCurveTo(914, 502, 350, 505, 178, 456);
      ctx.closePath();
    };
    drawCloud();
    ctx.fillStyle = 'rgba(255,255,255,.2)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(85,85,81,.76)';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    drawCloud();
    ctx.translate(3, 3);
    ctx.strokeStyle = 'rgba(115,115,111,.42)';
    ctx.lineWidth = 2.5;
    ctx.stroke();
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    return map;
  }, []);
  const textTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1240;
    canvas.height = 560;
    const ctx = canvas.getContext('2d');
    ctx.textAlign = 'center';
    ctx.fillStyle = 'rgba(76,76,72,.86)';
    ctx.font = '500 38px "Microsoft YaHei", sans-serif';
    ctx.fillText('大连理工大学在读，喜欢把点子变成能体验的产品。', 620, 225);
    ctx.fillText('沿着走廊走走，推开门认识不同面向的我。', 620, 284);
    ctx.font = '500 34px "Microsoft YaHei", sans-serif';
    ctx.fillText('开始探索  ↓', 620, 365);
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    return map;
  }, []);
  useEffect(() => () => { outlineTexture.dispose(); textTexture.dispose(); }, [outlineTexture, textTexture]);
  useEffect(() => {
    const cloud = cloudRef.current;
    const outline = outlineRef.current;
    const text = textRef.current;
    if (!visible || !cloud || !outline || !text) return undefined;
    const enter = gsap.timeline();
    enter.to(cloud.scale, { x: 1, y: 1, z: 1, duration: 0.35, ease: 'power2.out' }, 0);
    enter.to(outline, { opacity: 1, duration: 0.25, ease: 'sine.out' }, 0);
    enter.to(text.material, { opacity: 1, duration: 0.25, ease: 'sine.out' }, 0);
    return () => enter.kill();
  }, [visible]);
  useEffect(() => {
    const cloud = cloudRef.current;
    const text = textRef.current;
    if (!cloud || !text) return undefined;
    if (!started) {
      const resetCloud = gsap.to(cloud.position, { y: 1.4, duration: 0.8, ease: 'power2.out' });
      const restoreText = gsap.to(text.material, { opacity: 1, duration: 0.55, ease: 'sine.out' });
      return () => { resetCloud.kill(); restoreText.kill(); };
    }
    const lift = gsap.to(cloud.position, { y: 4.35, duration: 2.25, ease: 'sine.inOut' });
    const fade = gsap.to(text.material, { opacity: 0.2, duration: 0.7, ease: 'sine.inOut' });
    return () => { lift.kill(); fade.kill(); };
  }, [started]);
  return <group ref={cloudRef} position={[-4.2, 1.4, -4.8]} scale={1} visible={visible}>
    <mesh>
      <planeGeometry args={[8.2, 3.71]} />
      <meshBasicMaterial ref={outlineRef} map={outlineTexture} transparent opacity={0} depthWrite={false} side={THREE.DoubleSide} />
    </mesh>
    <mesh ref={textRef} position={[0, 0, 0.015]}>
      <planeGeometry args={[8.2, 3.71]} />
      <meshBasicMaterial map={textTexture} transparent depthWrite={false} side={THREE.DoubleSide} />
    </mesh>
    <mesh position={[0, -0.56, 0.03]} onClick={(event) => { event.stopPropagation(); onStart(); }} onPointerOver={() => { document.body.style.cursor = 'pointer'; }} onPointerOut={() => { document.body.style.cursor = 'auto'; }}>
      <planeGeometry args={[2.8, 0.65]} />
      <meshBasicMaterial transparent opacity={0} colorWrite={false} />
    </mesh>
  </group>;
}

function Door({ room, onOpen, active }) {
  const leaf = useRef();
  const sign = useRef();
  const doorTint = {
    intent: '#f7f6f1', education: '#dfc49a', projects: '#8f6d4c',
    campus: '#a9bca8', skills: '#adc0cf', profile: '#d5aaa1', 'unlock-real': '#f0eee8',
  }[room.id] || '#e2d2b5';
  const woodTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(92,88,80,.16)';
    ctx.lineWidth = 2.4;
    for (let x = 22; x < canvas.width; x += 64) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.bezierCurveTo(x - 9, 280, x + 12, 640, x - 4, canvas.height);
      ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(255,255,255,.42)';
    ctx.lineWidth = 4;
    for (let x = 42; x < canvas.width; x += 95) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.bezierCurveTo(x + 6, 330, x - 8, 720, x + 7, canvas.height);
      ctx.stroke();
    }
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    map.anisotropy = 4;
    return map;
  }, []);
  useEffect(() => () => woodTexture.dispose(), [woodTexture]);
  const enter = () => {
    if (active) return;
    const target = new THREE.Vector3(room.side < 0 ? -1.3 : 1.3, 1.48, room.z + 2.4);
    onOpen(room, target, leaf);
  };
  useFrame(({ clock }) => {
    if (sign.current) sign.current.rotation.z = Math.sin(clock.elapsedTime * 1.2 + Math.abs(room.z)) * 0.024;
  });
  return <group position={[room.side * 2.85, 0, room.z]} rotation={[0, room.side < 0 ? Math.PI / 2 : -Math.PI / 2, 0]} onClick={(e) => { e.stopPropagation(); enter(); }} onPointerOver={() => { document.body.style.cursor = 'pointer'; }} onPointerOut={() => { document.body.style.cursor = 'auto'; }}>
    <mesh position={[0, 1.18, 0]}><boxGeometry args={[1.28, 2.36, 0.12]} /><meshStandardMaterial color="#f0efeb" roughness={1} /></mesh>
    <group ref={leaf} position={[-0.54, 1.16, 0.085]}>
      <mesh position={[0.54, 0, 0.075]} onClick={(e) => { e.stopPropagation(); enter(); }} onPointerOver={() => { document.body.style.cursor = 'pointer'; }} onPointerOut={() => { document.body.style.cursor = 'auto'; }}>
        <planeGeometry args={[1.04, 2.12]} />
        <meshBasicMaterial transparent opacity={0} colorWrite={false} depthWrite={false} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[0.54, 0, 0]}><boxGeometry args={[1.08, 2.17, 0.08]} /><meshStandardMaterial map={woodTexture} color={doorTint} roughness={1} /></mesh>
      {[-0.82, 0.48].map((centerY) => <group key={centerY} position={[0.54, centerY, 0.047]}>
        <mesh><boxGeometry args={[0.8, 0.68, 0.028]} /><meshStandardMaterial color="#aaa69d" roughness={1} /></mesh>
        <mesh position={[0, 0, 0.016]}><boxGeometry args={[0.75, 0.63, 0.016]} /><meshStandardMaterial map={woodTexture} color={doorTint} roughness={1} /></mesh>
        {[-0.34, 0.34].map((x) => <mesh key={`side-${x}`} position={[x, 0, 0.027]}><boxGeometry args={[0.018, 0.57, 0.012]} /><meshStandardMaterial color="#8d8981" roughness={1} /></mesh>)}
        {[-0.29, 0.29].map((y) => <mesh key={`rail-${y}`} position={[0, y, 0.027]}><boxGeometry args={[0.69, 0.018, 0.012]} /><meshStandardMaterial color="#8d8981" roughness={1} /></mesh>)}
      </group>)}
      <mesh position={[0.94, 0, 0.072]}><sphereGeometry args={[0.045, 14, 12]} /><meshStandardMaterial color="#858078" roughness={0.82} /></mesh>
      <mesh position={[0.86, 0, 0.072]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.018, 0.018, 0.14, 8]} /><meshStandardMaterial color="#858078" roughness={0.82} /></mesh>
      {[-0.88, -0.12, 0.88].map((y) => <group key={`hinge-${y}`} position={[0.035, y, 0.057]}><mesh><boxGeometry args={[0.055, 0.16, 0.025]} /><meshStandardMaterial color="#8b8881" roughness={0.88} /></mesh><mesh position={[0, 0, 0.014]}><boxGeometry args={[0.025, 0.12, 0.008]} /><meshStandardMaterial color="#d4d2cc" /></mesh></group>)}
      <group ref={sign} position={[0.54, 0.91, 0.13]}>
        <mesh position={[0, 0.015, 0]}><torusGeometry args={[0.045, 0.009, 6, 16]} /><meshStandardMaterial color="#777774" roughness={0.95} /></mesh>
        <mesh position={[-0.165, -0.16, -0.005]} rotation={[0, 0, -Math.PI / 4]}><cylinderGeometry args={[0.007, 0.007, 0.46, 6]} /><meshStandardMaterial color="#777774" roughness={1} /></mesh>
        <mesh position={[0.165, -0.16, -0.005]} rotation={[0, 0, Math.PI / 4]}><cylinderGeometry args={[0.007, 0.007, 0.46, 6]} /><meshStandardMaterial color="#777774" roughness={1} /></mesh>
        <DoorSign label={room.label} />
      </group>
    </group>
  </group>;
}

function Corridor({ onRoomOpen, activeRoom, onController, started, introReady, onStart, resetKey }) {
  const { camera } = useThree();
  const positionRef = useRef(new THREE.Vector3(0, 1.5, 3.9));
  const lookAtRef = useRef(new THREE.Vector3(0, 1.48, -2.1));
  const activeLeafRef = useRef(null);
  const activeEnterTimelineRef = useRef(null);
  const enteringRoomRef = useRef(false);
  const returningRef = useRef(false);
  const returnPoseRef = useRef(null);
  const normalLookAtRef = useRef(null);
  const isLookingAtDoorRef = useRef(false);
  const [avatarVisible, setAvatarVisible] = useState(true);
  const [avatarApproach, setAvatarApproach] = useState(null);
  const [lookHintRoom, setLookHintRoom] = useState(null);
  const [lookingDoorId, setLookingDoorId] = useState(null);

  useEffect(() => {
    onController((resetToStart = false) => {
      enteringRoomRef.current = false;
      gsap.killTweensOf(camera.position);
      gsap.killTweensOf(lookAtRef.current);
      activeEnterTimelineRef.current?.kill();
      activeEnterTimelineRef.current = null;
      if (activeLeafRef.current) gsap.killTweensOf(activeLeafRef.current.rotation);
      isLookingAtDoorRef.current = false;
      normalLookAtRef.current = null;
      setLookingDoorId(null);
      setLookHintRoom(null);
      const returnPose = returnPoseRef.current;
      returningRef.current = true;
      if (resetToStart) {
        const startPosition = new THREE.Vector3(0, 1.5, 3.9);
        setAvatarApproach(null);
        setAvatarVisible(true);
        positionRef.current.copy(startPosition);
        gsap.to(lookAtRef.current, { x: 0, y: 1.48, z: -2.1, duration: 0.85, ease: 'power2.inOut' });
        gsap.to(camera.position, {
          x: startPosition.x, y: startPosition.y, z: startPosition.z, duration: 0.85, ease: 'power2.inOut',
          onComplete: () => {
            returningRef.current = false;
            activeLeafRef.current = null;
            returnPoseRef.current = null;
          },
        });
        if (activeLeafRef.current) gsap.to(activeLeafRef.current.rotation, { y: 0, duration: 0.65, ease: 'power2.inOut' });
        return;
      }
      if (!returnPose) {
        setAvatarApproach(null);
        positionRef.current.set(0, 1.5, 3.9);
        lookAtRef.current.set(0, 1.48, -2.1);
        gsap.to(camera.position, {
          x: 0, y: 1.5, z: 3.9, duration: 0.8, ease: 'power2.inOut',
          onComplete: () => { returningRef.current = false; setAvatarVisible(true); },
        });
        return;
      }
      positionRef.current.copy(returnPose.position);
      lookAtRef.current.copy(returnPose.lookAt);
      setAvatarApproach(null);
      gsap.to(camera.position, {
        x: returnPose.position.x,
        y: returnPose.position.y,
        z: returnPose.position.z,
        duration: 0.8,
        ease: 'power2.inOut',
        onComplete: () => {
          returningRef.current = false;
          activeLeafRef.current = null;
          returnPoseRef.current = null;
          setAvatarVisible(true);
        },
      });
      if (activeLeafRef.current) gsap.to(activeLeafRef.current.rotation, { y: 0, duration: 0.55, ease: 'power2.inOut' });
    });
  }, [camera, onController]);

  useEffect(() => {
    const walk = (event) => {
      if (!activeRoom && !enteringRoomRef.current) {
        if (isLookingAtDoorRef.current) {
          gsap.killTweensOf(lookAtRef.current);
          isLookingAtDoorRef.current = false;
          normalLookAtRef.current = null;
          setLookingDoorId(null);
        }
        positionRef.current.z = THREE.MathUtils.clamp(positionRef.current.z - event.deltaY * 0.008, -33.2, 3.9);
      }
    };
    window.addEventListener('wheel', walk, { passive: true });
    return () => window.removeEventListener('wheel', walk);
  }, [activeRoom]);

  const lookAtDoor = (room) => {
    if (lookingDoorId === room.id && normalLookAtRef.current) {
      gsap.to(lookAtRef.current, {
        x: normalLookAtRef.current.x, y: normalLookAtRef.current.y, z: normalLookAtRef.current.z,
        duration: 0.65, ease: 'power2.inOut',
        onComplete: () => { isLookingAtDoorRef.current = false; normalLookAtRef.current = null; setLookingDoorId(null); },
      });
      return;
    }
    gsap.killTweensOf(lookAtRef.current);
    normalLookAtRef.current = lookAtRef.current.clone();
    isLookingAtDoorRef.current = true;
    setLookingDoorId(room.id);
    gsap.to(lookAtRef.current, { x: room.side * 2.85, y: 1.28, z: room.z, duration: 0.72, ease: 'power2.inOut' });
  };

  useFrame((_, delta) => {
    if (activeRoom?.id === 'projects' || activeRoom?.id === 'skills') return;
    if (!activeRoom && !enteringRoomRef.current) {
      // Keep the view pointed down the corridor as the camera moves. A fixed
      // look-at point makes the camera turn around after it passes that point.
      if (!isLookingAtDoorRef.current) lookAtRef.current.set(positionRef.current.x, 1.48, positionRef.current.z - 6);
      let nearestRoom = null;
      let nearestDistance = Infinity;
      for (const room of rooms) {
        const ahead = positionRef.current.z - room.z;
        if (ahead >= -0.3 && ahead <= 3.2 && ahead < nearestDistance) {
          nearestRoom = room;
          nearestDistance = ahead;
        }
      }
      if (nearestRoom?.id !== lookHintRoom?.id) setLookHintRoom(nearestRoom);
    }
    if (!enteringRoomRef.current && !returningRef.current) camera.position.lerp(positionRef.current, Math.min(1, delta * 1.7));
    camera.lookAt(lookAtRef.current);
  });

  const openDoor = (room, target, leafRef) => {
    if (activeRoom) return;
    gsap.killTweensOf(lookAtRef.current);
    isLookingAtDoorRef.current = false;
    normalLookAtRef.current = null;
    setLookingDoorId(null);
    setLookHintRoom(null);
    setAvatarVisible(true);
    setAvatarApproach([room.side * 2.05, -0.075, room.z + 0.55]);
    returnPoseRef.current = {
      position: camera.position.clone(),
      lookAt: lookAtRef.current.clone(),
    };
    enteringRoomRef.current = true;
    positionRef.current.copy(target);
      lookAtRef.current.set(room.side * 2.25, 1.45, room.z);
    activeLeafRef.current = leafRef.current;
    const direction = room.side < 0 ? 1 : -1;
    activeEnterTimelineRef.current = gsap.timeline({ onComplete: () => {
      activeEnterTimelineRef.current = null;
      setAvatarVisible(false);
      setAvatarApproach(null);
      onRoomOpen(room);
    } })
      .to(leafRef.current.rotation, { y: direction * 1.28, duration: 0.9, ease: 'power2.inOut' }, 0.2)
      .to(camera.position, { x: target.x, y: target.y, z: target.z, duration: 0.95, ease: 'power2.inOut' }, 0.48);
  };

  const floorBoards = Array.from({ length: 168 }, (_, i) => {
    const columns = 8;
    const row = Math.floor(i / columns);
    const column = i % columns;
    const stagger = row % 2 ? 0.72 : 0;
    return { x: -5.25 + column * 1.5 + stagger, z: 4 - row * 2.1 };
  });

  return <>
    <GreetingAvatar resetKey={resetKey} visible={avatarVisible} approachTarget={avatarApproach} lookHint={lookHintRoom} onLookAtDoor={lookAtDoor} lookingDoorId={lookingDoorId} />
    <color attach="background" args={['#f4f4f2']} />
    <fog attach="fog" args={['#f4f4f2', 20, 68]} />
    <ambientLight intensity={2.5} />
    <directionalLight position={[-3, 7, 5]} intensity={2.1} color="#fffef9" />
    <pointLight position={[0, 4, -31]} intensity={15} distance={28} color="#ffffff" />
    <mesh position={[0, -0.08, -15]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[13, 52]} /><meshStandardMaterial color="#f2f2ef" roughness={1} /></mesh>
    {floorBoards.map((board, i) => <mesh key={`plank-${i}`} position={[board.x, -0.065, board.z]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[1.46, 2.04]} /><meshStandardMaterial color={['#f8f8f6', '#f0f0ee', '#f5f5f2', '#ededeb'][i % 4]} roughness={1} /></mesh>)}
    {Array.from({ length: 17 }, (_, i) => <mesh key={`seam-${i}`} position={[0, -0.045, 2 - i * 3.05]}><boxGeometry args={[12.8, 0.008, 0.014]} /><meshStandardMaterial color="#b9b9b6" /></mesh>)}
    {[
      { position: [-4.8, 3.2, -8], scale: 1.55, rotation: 0.16 },
      { position: [4.9, 4.1, -13], scale: 1.05, rotation: -0.2 },
      { position: [-4.5, 4.6, -22], scale: 1.1, rotation: 0.08 },
      { position: [4.3, 3.6, -27], scale: 0.84, rotation: -0.12 },
      { position: [0.5, 4.3, -36], scale: 0.7, rotation: 0.04 },
    ].map((cloud) => <SketchCloud key={cloud.position.join('-')} {...cloud} />)}
    <FloatingIntroCloud visible={introReady} started={started} onStart={onStart} />
    {rooms.map((room) => <Door key={room.id} room={room} onOpen={openDoor} active={!!activeRoom} />)}
  </>;
}

function App() {
  const [room, setRoom] = useState(null);
  const [started, setStarted] = useState(false);
  const [resetKey, setResetKey] = useState(0);
  const homeRef = useRef(() => {});
  const registerHome = useCallback((home) => { homeRef.current = home; }, []);

  useEffect(() => { document.title = '陈江小鱼 · 个人介绍'; }, []);
  useEffect(() => {
    const closeOnEscape = (event) => { if (event.key === 'Escape' && room) closeRoom(); };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [room]);

  const closeRoom = () => { setRoom(null); homeRef.current?.(); };
  const returnToStart = () => {
    setRoom(null);
    setStarted(false);
    setResetKey((key) => key + 1);
    homeRef.current?.(true);
  };
  return <main className="site-shell">
    <Canvas className="scene-canvas" camera={{ position: [0, 1.5, 3.9], fov: 67, near: 0.1, far: 90 }} dpr={[1, 1.6]} gl={{ antialias: true, powerPreference: 'high-performance' }}>
      <Corridor onRoomOpen={setRoom} activeRoom={room} onController={registerHome} started={started} introReady onStart={() => setStarted(true)} resetKey={resetKey} />
    </Canvas>
    <div className="grain" aria-hidden="true" />
    <header className="topbar"><a className="brand" href="#top" onClick={(e) => { e.preventDefault(); closeRoom(); }}>陈江小鱼</a></header>
    {!room && <button className="return-start-button" onClick={returnToStart}>返回起点</button>}
    <div className={`welcome-bubble${started ? ' welcome-bubble--dismissed' : ' welcome-bubble--shown'}`} aria-live="polite">
      <svg viewBox="0 0 360 190" aria-hidden="true">
        <path d="M41 115C19 96 20 63 43 46 62 14 108 14 134 31 163 2 209 10 225 34 260 17 300 33 303 61 336 66 347 99 330 119 322 145 291 158 261 151 222 174 140 167 114 154 82 170 50 150 41 115Z" />
        <path className="bubble-sketch" d="M45 119C17 96 22 60 46 43 66 11 110 16 136 34 164 4 207 12 228 37 263 19 300 36 306 64 337 68 345 99 327 122 317 147 289 160 259 154 218 176 141 169 111 157 78 171 49 151 45 119Z" />
        <circle cx="318" cy="158" r="12" /><circle cx="341" cy="178" r="6" />
      </svg>
      <p>你好，我是<br /><strong>陈江小鱼</strong></p>
    </div>
    <div className="interaction-hint">滚动前进/后退 · 按住人物拖动转身</div>
    {room && !['projects', 'skills', 'unlock-real'].includes(room.id) && <div className="room-scrim" role="presentation"><article className="room-card" style={{ '--room-accent': room.color }}><button className="room-close" onClick={closeRoom} aria-label="返回走廊">×</button><span className="room-label">{room.label}</span><span className="room-icon">{room.icon}</span><h2>{room.title}</h2>{room.body && <p className="room-body">{room.body}</p>}{room.facts && <ul className="room-facts">{room.facts.map((fact) => <li key={fact}>{fact}</li>)}</ul>}{room.items && <div className="room-items">{room.items.map((item) => <section className="room-item" key={item.heading}><div className="item-heading">{item.heading}</div>{item.meta && <div className="item-meta">{item.meta}</div>}{item.text && <p>{item.text}</p>}{item.tags && <div className="item-tags">{item.tags}</div>}</section>)}</div>}<div className="room-rule" /><button className="back-button" onClick={closeRoom}>← 回到走廊</button></article></div>}
    {room?.id === 'projects' && <ProjectsGarden room={room} onClose={closeRoom} />}
    {room?.id === 'skills' && <SkillsRoom room={room} onClose={closeRoom} />}
    {room?.id === 'unlock-real' && <UnlockRealRoom onClose={closeRoom} />}
  </main>;
}

export default App;


