import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import './ProjectsGarden.css';

function GardenSign({ label }) {
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 180;
    const context = canvas.getContext('2d');
    context.fillStyle = '#f6eedf';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.strokeStyle = '#b69b72';
    context.lineWidth = 8;
    context.strokeRect(8, 8, canvas.width - 16, canvas.height - 16);
    context.fillStyle = '#4e493b';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    const chars = [...label];
    const lines = chars.length > 10 ? [chars.slice(0, 10).join(''), chars.slice(10, 20).join('')] : [label];
    const fontSize = lines.length > 1 ? 54 : 62;
    context.font = `700 ${fontSize}px "Microsoft YaHei", "Noto Sans CJK SC", sans-serif`;
    lines.forEach((line, index) => context.fillText(line, canvas.width / 2, lines.length > 1 ? 52 + index * 68 : 92, 590));
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    map.anisotropy = 4;
    return map;
  }, [label]);

  useEffect(() => () => texture.dispose(), [texture]);
  return <mesh position={[0, 2.75, 0.45]}>
    <planeGeometry args={[1.65, 0.47]} />
    <meshBasicMaterial map={texture} toneMapped={false} />
  </mesh>;
}

function FlowerPot({ item, position, color, selected, onSelect }) {
  const flower = useRef();
  useFrame((_, delta) => {
    if (!flower.current) return;
    const target = selected ? 1.42 : 1;
    const next = THREE.MathUtils.damp(flower.current.scale.x, target, 5, delta);
    flower.current.scale.setScalar(next);
  });

  const bloom = (event) => {
    event.stopPropagation();
    onSelect(item);
  };

  return <group position={position} onClick={bloom} onPointerOver={() => { document.body.style.cursor = 'pointer'; }} onPointerOut={() => { document.body.style.cursor = 'auto'; }}>
    <mesh position={[0, 0.38, 0]} castShadow receiveShadow>
      <cylinderGeometry args={[0.48, 0.35, 0.66, 20]} />
      <meshStandardMaterial color={['#d5a08c', '#d7bd83', '#a8b9a0'][Math.abs(position[0] + position[2]) % 3 | 0]} roughness={0.9} />
    </mesh>
    <mesh position={[0, 0.73, 0]}>
      <cylinderGeometry args={[0.39, 0.39, 0.06, 20]} />
      <meshStandardMaterial color="#66533f" roughness={1} />
    </mesh>
    <group ref={flower}>
      <mesh position={[0, 1.25, 0]} castShadow>
        <cylinderGeometry args={[0.035, 0.055, 1.12, 8]} />
        <meshStandardMaterial color="#66875a" roughness={0.9} />
      </mesh>
      <mesh position={[-0.2, 1.08, 0]} rotation={[0, 0, 0.62]} scale={[0.3, 0.11, 0.1]}>
        <sphereGeometry args={[1, 14, 10]} />
        <meshStandardMaterial color="#7e9c66" roughness={0.9} />
      </mesh>
      <mesh position={[0.19, 1.38, 0]} rotation={[0, 0, -0.6]} scale={[0.28, 0.1, 0.09]}>
        <sphereGeometry args={[1, 14, 10]} />
        <meshStandardMaterial color="#8eaa70" roughness={0.9} />
      </mesh>
      {Array.from({ length: 8 }, (_, index) => {
        const angle = (index / 8) * Math.PI * 2;
        return <mesh key={index} position={[Math.cos(angle) * 0.28, 1.82 + Math.sin(angle) * 0.28, 0]} rotation={[0, 0, angle + Math.PI / 2]} scale={[0.17, 0.32, 0.12]} castShadow>
          <sphereGeometry args={[1, 16, 12]} />
          <meshStandardMaterial color={color} roughness={0.72} />
        </mesh>;
      })}
      <mesh position={[0, 1.82, 0.02]} castShadow>
        <sphereGeometry args={[0.22, 18, 14]} />
        <meshStandardMaterial color="#e9bd68" roughness={0.58} />
      </mesh>
    </group>
    <mesh position={[0, 2.42, 0.44]}>
      <cylinderGeometry args={[0.025, 0.025, 0.72, 8]} />
      <meshStandardMaterial color="#98794f" />
    </mesh>
    <GardenSign label={item.heading} />
  </group>;
}

function GardenTree({ position, scale = 1 }) {
  return <group position={position} scale={scale}>
    <mesh position={[0, 1.1, 0]} castShadow>
      <cylinderGeometry args={[0.17, 0.24, 2.2, 10]} />
      <meshStandardMaterial color="#987a57" roughness={1} />
    </mesh>
    {[[0, 2.3, 0], [-0.48, 2.05, 0.04], [0.47, 2.08, 0.02], [0, 2.68, 0.02]].map(([x, y, z], index) => <mesh key={index} position={[x, y, z]} scale={index === 3 ? 0.76 : 1} castShadow>
      <sphereGeometry args={[0.75, 16, 14]} />
      <meshStandardMaterial color={index % 2 ? '#91ad78' : '#a5bb86'} roughness={0.9} />
    </mesh>)}
  </group>;
}

function GardenWorld({ projects, selectedProject, onSelect }) {
  const { camera } = useThree();
  useEffect(() => {
    camera.position.set(0, 5.4, 11.8);
    camera.lookAt(0, 1, 0);
    camera.updateProjectionMatrix();
  }, [camera]);

  const positions = [
    [-3.65, 0, -2.6], [3.65, 0, -2.6],
    [-3.65, 0, 0], [3.65, 0, 0],
    [-3.65, 0, 2.6], [3.65, 0, 2.6],
  ];
  const colors = ['#e7a0a1', '#9fadd0', '#e2b86e', '#bb9dc5', '#df8f75', '#91b7a0'];

  return <>
    <color attach="background" args={['#dbe8d1']} />
    <fog attach="fog" args={['#dbe8d1', 18, 36]} />
    <ambientLight intensity={1.65} />
    <directionalLight position={[-4, 10, 6]} intensity={2} color="#fff6df" castShadow />
    <mesh position={[0, -0.14, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[50, 50]} />
      <meshStandardMaterial color="#b8ca99" roughness={1} />
    </mesh>
    <mesh position={[0, -0.08, -8]} scale={[8, 2.4, 1.4]}>
      <sphereGeometry args={[1, 24, 18]} />
      <meshStandardMaterial color="#cad7ad" roughness={1} />
    </mesh>
    <mesh position={[-9, -0.02, -5]} scale={[6, 2.2, 2]}>
      <sphereGeometry args={[1, 20, 16]} />
      <meshStandardMaterial color="#c2d2a6" roughness={1} />
    </mesh>
    <mesh position={[9, 0, -7]} scale={[7, 2.8, 2]}>
      <sphereGeometry args={[1, 20, 16]} />
      <meshStandardMaterial color="#c4d4a9" roughness={1} />
    </mesh>
    {[-8, 8].map((x) => [-4, 2, 7].map((z, index) => <GardenTree key={`${x}-${z}`} position={[x, 0, z]} scale={index === 1 ? 0.85 : 1} />))}
    {Array.from({ length: 9 }, (_, index) => <mesh key={`stone-${index}`} position={[Math.sin(index * 0.75) * 0.7, 0.015, 5.7 - index * 1.5]} rotation={[-Math.PI / 2, 0, index % 2 ? 0.15 : -0.1]}>
      <circleGeometry args={[0.44, 18]} />
      <meshStandardMaterial color="#e7ddc4" roughness={1} />
    </mesh>)}
    {projects.map((item, index) => <FlowerPot
      key={item.heading}
      item={item}
      position={positions[index]}
      color={colors[index]}
      selected={selectedProject?.heading === item.heading}
      onSelect={onSelect}
    />)}
  </>;
}

export default function ProjectsGarden({ room, onClose }) {
  const [selectedProject, setSelectedProject] = useState(null);
  const projects = room.items || [];

  return <section className="projects-garden" aria-label="项目花园">
    <Canvas shadows camera={{ position: [0, 5.4, 11.8], fov: 48, near: 0.1, far: 100 }} dpr={[1, 1.5]} gl={{ antialias: true, powerPreference: 'high-performance' }}>
      <GardenWorld projects={projects} selectedProject={selectedProject} onSelect={setSelectedProject} />
    </Canvas>
    <header className="garden-header">
      <button type="button" className="garden-back" onClick={onClose}>← 回到走廊</button>
      <div><span className="garden-eyebrow">项目经历 · 花园</span><h1>项目花园</h1></div>
      <p>点一盆花，看看它代表的项目</p>
    </header>
    {selectedProject && <article className="garden-project-card" key={selectedProject.heading}>
      <button className="garden-project-close" type="button" onClick={() => setSelectedProject(null)} aria-label="关闭项目详情">×</button>
      <span className="garden-project-label">{selectedProject.meta || '项目经历'}</span>
      <h2>{selectedProject.heading}</h2>
      <p>{selectedProject.text}</p>
      {selectedProject.tags && <div className="garden-project-tags">{selectedProject.tags}</div>}
      {selectedProject.url
        ? <a className="garden-project-link" href={selectedProject.url} target="_blank" rel="noreferrer">查看项目 ↗</a>
        : <span className="garden-project-link garden-project-link--pending">项目链接待补充</span>}
    </article>}
  </section>;
}
