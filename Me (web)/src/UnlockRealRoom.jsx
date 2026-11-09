import { useEffect, useState } from 'react';
import './UnlockRealRoom.css';
import { publicAsset } from './utils/publicAsset.js';

const gallery = [
  { title: '3D人物原型', caption: '把熟悉的自己，做成可以进入三维空间的角色。', image: publicAsset('unlock-real/prototype.jpg'), position: 'card--prototype' },
  { title: '滑雪', caption: '8岁开始滑雪，熟练单板、双板，坚持热爱。', image: publicAsset('unlock-real/skiing.jpg'), position: 'card--ski' },
  { title: '羽毛球', caption: '在球场上接住每一次来球。', image: publicAsset('unlock-real/badminton.jpg'), position: 'card--badminton' },
  { title: '篮球', caption: '和队友一起跑动、传球、投篮。', image: publicAsset('unlock-real/basketball.jpg'), position: 'card--basketball' },
  { title: '攀岩', caption: '沿着路线向上，试着突破自己的高度。', image: publicAsset('unlock-real/climbing.jpg'), position: 'card--climbing' },
  { title: '卡丁车', caption: '坐进驾驶舱，体验赛道上的速度。', image: publicAsset('unlock-real/karting.jpg'), position: 'card--karting' },
  { title: '高尔夫', caption: '在夜色中挥杆，感受击球的节奏。', image: publicAsset('unlock-real/golf.jpg'), position: 'card--golf' },
  { title: '花样滑冰', caption: '在冰面上练习平衡与旋转。', image: publicAsset('unlock-real/figure-skating.jpg'), position: 'card--skating' },
  { title: '保龄球', caption: '瞄准球道，等待球瓶倒下的瞬间。', image: publicAsset('unlock-real/bowling.jpg'), position: 'card--bowling' },
  { title: '滑板', caption: '在路面上练习动作，享受滑行。', image: publicAsset('unlock-real/skateboarding.jpg'), position: 'card--skateboarding' },
];

export default function UnlockRealRoom({ onClose }) {
  const [active, setActive] = useState(null);
  useEffect(() => {
    const close = (event) => { if (event.key === 'Escape') active ? setActive(null) : onClose(); };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, [active, onClose]);

  return <section className={`unlock-room${active ? ' unlock-room--focused' : ''}`} aria-label="解锁真人">
    <header className="unlock-room__header">
      <button className="unlock-room__back" onClick={onClose}>← 回到走廊</button>
      <div className="unlock-room__heading"><span>BEYOND THE AVATAR</span><h1>解锁真人</h1><p>从3D人物原型到日常运动，看看镜头之外的我。</p></div>
      <span className="unlock-room__count">{String(gallery.length).padStart(2, '0')} MOMENTS</span>
    </header>
    <div className="unlock-room__space">
      <div className="unlock-room__orbit unlock-room__orbit--one" />
      <div className="unlock-room__orbit unlock-room__orbit--two" />
      {gallery.map((item, index) => <button key={item.title} className={`unlock-tile ${item.position}${active === item ? ' is-active' : ''}`} style={{ '--tile-order': index }} onClick={() => setActive(item)} aria-label={`查看：${item.title}`}>
        <img src={item.image} alt={item.title} loading="lazy" />
        <span className="unlock-tile__label">{item.title}</span>
      </button>)}
      <div className="unlock-room__hint">点击图像 · 靠近看看</div>
    </div>
    {active && <div className="unlock-focus" role="dialog" aria-modal="true" aria-label={active.title} onClick={() => setActive(null)}>
      <article className="unlock-focus__card" onClick={(event) => event.stopPropagation()}>
        <button className="unlock-focus__close" onClick={() => setActive(null)} aria-label="关闭">×</button>
        <img src={active.image} alt={active.title} />
        <div className="unlock-focus__copy"><span>PERSONAL MOMENT</span><h2>{active.title}</h2><p>{active.caption}</p><div className="unlock-focus__index">{String(gallery.indexOf(active) + 1).padStart(2, '0')} / {String(gallery.length).padStart(2, '0')}</div></div>
      </article>
      <button className="unlock-focus__previous" onClick={(event) => { event.stopPropagation(); setActive(gallery[(gallery.indexOf(active) + gallery.length - 1) % gallery.length]); }} aria-label="上一张">←</button>
      <button className="unlock-focus__next" onClick={(event) => { event.stopPropagation(); setActive(gallery[(gallery.indexOf(active) + 1) % gallery.length]); }} aria-label="下一张">→</button>
    </div>}
  </section>;
}

