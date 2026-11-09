import { useEffect, useMemo, useRef, useState } from 'react';
import gsap from 'gsap';
import './SkillsRoom.css';

const CHIME_LAYOUT = [
  { label: '编程语言', x: 18, line: '22vh', tone: 'lilac', detailIndex: 0 },
  { label: '专业能力', x: 43, line: '27vh', tone: 'cream', detailIndex: 1 },
  { label: '常用工具', x: 68, line: '16vh', tone: 'rose', detailIndex: 2 },
  { label: '', x: 87, line: '28vh', tone: 'blue', detailIndex: -1 },
];

const FAR_CHIMES = [
  { x: 6, line: '26vh', tone: 'yellow' },
  { x: 30, line: '16vh', tone: 'blue' },
  { x: 76, line: '18vh', tone: 'green' },
  { x: 96, line: '25vh', tone: 'yellow' },
];

const BACK_CHIMES = [34, 45, 55, 66, 77].map((x, index) => ({ x, line: `${5 + (index % 2) * 2}vh`, tone: ['blue', 'green', 'yellow', 'blue', 'green'][index] }));

function PaperPlane() {
  return <svg viewBox="0 0 120 100" role="presentation">
    <path className="plane-shadow" d="M8 36 111 7 78 92 57 58 8 36Z" />
    <path className="plane-main" d="M8 36 111 7 78 92 57 58 8 36Z" />
    <path className="plane-fold" d="m57 58 54-51-33 85-21-34Z" />
    <path className="plane-crease" d="M57 58 111 7" />
  </svg>;
}

export default function SkillsRoom({ room, onClose }) {
  const rootRef = useRef(null);
  const planeRef = useRef(null);
  const [selectedSkill, setSelectedSkill] = useState(null);
  const skillDetails = useMemo(() => [
    { title: '编程语言', text: 'C，C++，python' },
    { title: '专业能力', text: '需求拆解、交互设计与产品原型迭代；具备编程基础，能使用 AI 工具辅助开发、调试与快速学习新技术。' },
    { title: '常用工具', text: '生成式 AI 与信息检索：ChatGPT、Grok、Perplexity\nAI 辅助编程：Codex\n开发与代码协作：GitHub\n三维建模与 AI 生成：Meshy、ZOOOP\n办公软件：Excel（自学函数）、WPS\n灵感库：Uiverse、MotionSites' },
  ], []);

  const openSkillCard = (event, detail) => {
    const root = rootRef.current;
    if (!root) return;
    const bounds = root.getBoundingClientRect();
    const paper = event.currentTarget.getBoundingClientRect();
    const cardWidth = Math.min(420, bounds.width - 24);
    const cardHeight = Math.min(320, bounds.height - 24);
    const paperLeft = paper.left - bounds.left;
    let left = paper.right - bounds.left + 22;
    if (left + cardWidth > bounds.width - 12) left = paperLeft - cardWidth - 22;
    left = Math.max(12, Math.min(left, bounds.width - cardWidth - 12));
    let top = paper.top - bounds.top + paper.height / 2 - cardHeight / 2;
    top = Math.max(12, Math.min(top, bounds.height - cardHeight - 12));
    setSelectedSkill({ ...detail, cardLeft: left, cardTop: top });
  };

  useEffect(() => {
    const root = rootRef.current;
    const plane = planeRef.current;
    if (!root || !plane) return undefined;

    const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const initialBounds = root.getBoundingClientRect();
    gsap.set(plane, { x: initialBounds.width / 2, y: initialBounds.height / 2, xPercent: -50, yPercent: -50 });
    const media = gsap.matchMedia(root);
    media.add('(prefers-reduced-motion: no-preference)', () => {
      root.querySelectorAll('.skills-chime-swing').forEach((chime, index) => {
        const direction = index % 2 === 0 ? 1 : -1;
        gsap.to(chime, {
          rotation: direction * 4.2, y: index % 2 ? 2 : -2,
          duration: 3.1, delay: index * 0.16,
          repeat: -1, yoyo: true, ease: 'sine.inOut', transformOrigin: '50% 0%',
        });
      });
      gsap.to(root.querySelector('.skills-sun-rays'), { rotation: 360, duration: 74, repeat: -1, ease: 'none' });
      gsap.to(root.querySelector('.skills-light-glow'), { x: '9vw', y: '4vh', duration: 8, repeat: -1, yoyo: true, ease: 'sine.inOut' });
    }, root);

    const moveX = gsap.quickTo(plane, 'x', { duration: motionPreference ? 0.06 : 0.72, ease: 'power3.out' });
    const moveY = gsap.quickTo(plane, 'y', { duration: motionPreference ? 0.06 : 0.78, ease: 'power2.out' });
    const tilt = gsap.quickTo(plane, 'rotation', { duration: 0.45, ease: 'power2.out' });
    const onPointerMove = (event) => {
      const bounds = root.getBoundingClientRect();
      const px = (event.clientX - bounds.left) / bounds.width;
      const py = (event.clientY - bounds.top) / bounds.height;
      moveX(px * bounds.width);
      moveY(py * bounds.height);
      tilt((px - 0.5) * 16);
    };
    const onPointerLeave = () => {
      const bounds = root.getBoundingClientRect();
      moveX(bounds.width / 2); moveY(bounds.height / 2); tilt(0);
    };
    root.addEventListener('pointermove', onPointerMove);
    root.addEventListener('pointerleave', onPointerLeave);

    return () => {
      root.removeEventListener('pointermove', onPointerMove);
      root.removeEventListener('pointerleave', onPointerLeave);
      moveX.tween.kill();
      moveY.tween.kill();
      tilt.tween.kill();
      media.revert();
    };
  }, []);

  return <section ref={rootRef} className="skills-room" aria-label="相关技能风铃房间">
    <img className="skills-room-background" src="/skills-open-gallery.svg" alt="开放的手绘天空与透视地面" />
    <div className="skills-sun-rays" aria-hidden="true" />
    <div className="skills-light-glow" aria-hidden="true" />
    <svg className="skills-breeze-lines" viewBox="0 0 1600 900" preserveAspectRatio="none" aria-hidden="true">
      <path d="M-80 260 C260 180 360 390 700 285 S1260 180 1700 330" />
      <path d="M-80 510 C220 420 480 570 760 475 S1290 390 1700 540" />
      <path d="M-80 660 C260 580 460 730 800 630 S1330 570 1700 700" />
    </svg>
    {FAR_CHIMES.map((chime, index) => <div key={`far-${chime.x}`} className="skills-chime skills-chime--far" style={{ left: `${chime.x}%`, top: 0, '--string-length': chime.line }} aria-hidden="true">
      <div className="skills-chime-swing">
        <span className="skills-chime-string" />
        <span className="skills-chime-finial"><i /><i /><i /></span>
        <span className="skills-chime-bell"><i /></span>
        <span className="skills-chime-clapper" />
        <span className="skills-chime-paper-string" />
        <span className={`skills-chime-paper skills-chime-paper--${chime.tone}`} />
      </div>
    </div>)}
    {BACK_CHIMES.map((chime, index) => <div key={`back-${chime.x}`} className="skills-chime skills-chime--far skills-chime--back" style={{ left: `${chime.x}%`, top: `${31 + (index % 2) * 2}%`, '--string-length': chime.line }} aria-hidden="true">
      <div className="skills-chime-swing">
        <span className="skills-chime-string" />
        <span className="skills-chime-finial"><i /><i /><i /></span>
        <span className="skills-chime-bell"><i /></span>
        <span className="skills-chime-clapper" />
        <span className="skills-chime-paper-string" />
        <span className={`skills-chime-paper skills-chime-paper--${chime.tone}`} />
      </div>
    </div>)}
    {CHIME_LAYOUT.map((chime, index) => {
      const detail = chime.detailIndex >= 0 ? skillDetails[chime.detailIndex] : null;
      return <div key={chime.x} className={`skills-chime skills-chime--${index + 1}`} style={{ left: `${chime.x}%`, top: 0, '--string-length': chime.line }}>
        <div className="skills-chime-swing">
          <span className="skills-chime-string" />
          <span className="skills-chime-finial"><i /><i /><i /></span>
          <span className="skills-chime-bell"><i /></span>
          <span className="skills-chime-clapper" />
          <span className="skills-chime-paper-string" />
          {detail
            ? <button className={`skills-chime-paper skills-chime-paper--${chime.tone}`} type="button" onClick={(event) => openSkillCard(event, detail)}>{chime.label}</button>
            : <span className={`skills-chime-paper skills-chime-paper--${chime.tone}`} aria-label="空白纸片" />}
        </div>
      </div>;
    })}
    <button className="skills-room-back" type="button" onClick={onClose}>← 回到走廊</button>
    <div ref={planeRef} className="skills-paper-plane" aria-hidden="true"><PaperPlane /></div>
    {selectedSkill && <aside className="skills-detail-card" style={{ left: selectedSkill.cardLeft, top: selectedSkill.cardTop }}>
      <button type="button" className="skills-detail-close" onClick={() => setSelectedSkill(null)} aria-label="关闭技能详情">×</button>
      <span>相关技能</span><h2>{selectedSkill.title}</h2><p>{selectedSkill.text}</p>
    </aside>}
  </section>;
}
