import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Html, useAnimations, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { clone } from 'three/addons/utils/SkeletonUtils.js';

const MODEL_URL = `${import.meta.env.BASE_URL}models/pigtail-girl.glb`;
const RESTING_HEIGHT = 1.0875;

export default function GreetingAvatar({ resetKey = 0, visible = true, approachTarget = null, lookHint = null, onLookAtDoor, lookingDoorId = null }) {
  const anchor = useRef(null);
  const turntable = useRef(null);
  const drag = useRef(null);
  const activityTimer = useRef(null);
  const approachState = useRef(null);
  const bones = useRef(null);
  const greetingComplete = true;
  const [motion, setMotion] = useState('idle');
  const [showDragHint, setShowDragHint] = useState(true);
  const clipMotionActive = useRef(false);
  const { camera, size } = useThree();
  const { scene, animations } = useGLTF(MODEL_URL);
  const model = useMemo(() => clone(scene), [scene]);
  const { actions } = useAnimations(animations, model);
  const modelFit = useMemo(() => {
    const bounds = new THREE.Box3().setFromObject(model);
    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());
    const height = bounds.max.y - bounds.min.y;
    return {
      scale: height > 0 ? RESTING_HEIGHT / height : 1,
      sourceHeight: height,
      footOffset: -bounds.min.y,
      hitSize: [Math.max(size.x * 1.35, height * 0.55), Math.max(height * 1.15, 0.1), Math.max(size.z * 2.4, height * 0.38)],
      hitCenter: [center.x, height * 0.52, center.z],
    };
  }, [model]);

  useEffect(() => {
    window.clearTimeout(activityTimer.current);
    drag.current = null;
    setMotion('idle');
    setShowDragHint(true);
    if (turntable.current) turntable.current.rotation.set(0, 0, 0);
  }, [resetKey]);

  useEffect(() => {
    const findBone = (name) => model.getObjectByName(`mixamorig:${name}`) || model.getObjectByName(name);
    const arm = findBone('RightArm');
    const leftLeg = findBone('LeftUpLeg');
    const rightLeg = findBone('RightUpLeg');
    const leftArm = findBone('LeftArm');
    bones.current = {
      arm,
      leftLeg,
      rightLeg,
      leftArm,
      armX: arm?.rotation.x ?? 0,
      leftArmX: leftArm?.rotation.x ?? 0,
      leftLegX: leftLeg?.rotation.x ?? 0,
      rightLegX: rightLeg?.rotation.x ?? 0,
    };
  }, [model]);

  const beginDrag = useCallback((event) => {
    event.stopPropagation();
    try { event.target.setPointerCapture?.(event.pointerId); } catch { /* window pointer tracking remains active */ }
    drag.current = { x: event.clientX, y: event.clientY, startYaw: turntable.current?.rotation.y ?? 0 };
    document.body.style.cursor = 'grabbing';
  }, []);
  const endDrag = useCallback(() => {
    drag.current = null;
    document.body.style.cursor = 'auto';
  }, []);

  useEffect(() => {
    const markMotion = (next) => {
      setMotion(next);
      window.clearTimeout(activityTimer.current);
      activityTimer.current = window.setTimeout(() => setMotion('idle'), 420);
    };
    const onPointerMove = (event) => {
      if (drag.current && turntable.current) {
        const dx = event.clientX - drag.current.x;
        const dy = event.clientY - drag.current.y;
        drag.current = { ...drag.current, x: event.clientX, y: event.clientY };
        turntable.current.rotation.y += dx * 0.012;
        turntable.current.rotation.x = THREE.MathUtils.clamp(turntable.current.rotation.x + dy * 0.008, -0.22, 0.22);
        if (Math.abs(turntable.current.rotation.y - drag.current.startYaw) >= Math.PI / 6) setShowDragHint(false);
      }
    };
    const onWheel = (event) => {
      if (!greetingComplete) return;
      markMotion(Math.abs(event.deltaY) > 48 ? 'run' : 'walk');
    };
    const onPointerUp = () => endDrag();
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
    window.addEventListener('wheel', onWheel, { passive: true });
    return () => {
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
      window.removeEventListener('wheel', onWheel);
      window.clearTimeout(activityTimer.current);
    };
  }, [endDrag, greetingComplete]);

  useEffect(() => {
    if (!greetingComplete) return;
    const walking = actions.Walking || Object.entries(actions).find(([name]) => name.toLowerCase().includes('walk'))?.[1];
    const running = actions.Running || Object.entries(actions).find(([name]) => name.toLowerCase().includes('run'))?.[1];
    const selected = approachTarget ? walking : motion === 'run' ? running : motion === 'walk' ? walking : null;
    clipMotionActive.current = false;
    for (const action of Object.values(actions)) {
      if (!action) continue;
      if (action === selected) {
        action.enabled = true;
        action.reset().setLoop(THREE.LoopRepeat, Infinity).setEffectiveWeight(1).setEffectiveTimeScale(motion === 'run' && !approachTarget ? 1.05 : 0.65).fadeIn(0.18).play();
        clipMotionActive.current = action.isRunning();
      } else {
        action.fadeOut(0.18);
      }
    }
    return () => { for (const action of Object.values(actions)) action?.fadeOut(0.12); };
  }, [actions, approachTarget, greetingComplete, motion]);

  useFrame((state) => {
    if (!anchor.current) return;
    const direction = camera.getWorldDirection(new THREE.Vector3()).setY(0).normalize();
    // Camera-right is up × forward. Keep the avatar on the right side of the welcome cloud.
    const right = new THREE.Vector3(-direction.z, 0, direction.x).normalize();
    if (approachTarget) {
      const target = new THREE.Vector3(...approachTarget);
      if (!approachState.current) approachState.current = { target, position: anchor.current.position.clone() };
      const travel = approachState.current;
      if (!travel.target.equals(target)) travel.target.copy(target);
      const distanceToDoor = travel.position.distanceTo(target);
      travel.position.lerp(target, Math.min(1, delta * 4.4 / Math.max(distanceToDoor, 0.001)));
      anchor.current.position.copy(travel.position);
      const dx = target.x - travel.position.x;
      const dz = target.z - travel.position.z;
      anchor.current.rotation.y = Math.atan2(dx, dz);
    } else {
      approachState.current = null;
      anchor.current.position.set(
        camera.position.x + right.x * 0.95 + direction.x * 2.75,
        -0.075,
        camera.position.z + right.z * 0.95 + direction.z * 2.75,
      );
      anchor.current.rotation.y = Math.atan2(-direction.x, -direction.z);
    }
    if (turntable.current) {
      const distance = camera.position.distanceTo(anchor.current.position);
      const viewHeight = 2 * distance * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      const eightCmInCssPixels = 8 * 96 / 2.54;
      const screenCalibratedScale = viewHeight * eightCmInCssPixels / Math.max(size.height, 1) / Math.max(modelFit.sourceHeight, 0.001);
      turntable.current.scale.setScalar(screenCalibratedScale);
    }

    const rig = bones.current;
    if (greetingComplete && !clipMotionActive.current && rig) {
      if (motion === 'idle') {
        if (rig.leftLeg) rig.leftLeg.rotation.x = rig.leftLegX;
        if (rig.rightLeg) rig.rightLeg.rotation.x = rig.rightLegX;
        if (rig.leftArm) rig.leftArm.rotation.x = rig.leftArmX;
        if (rig.arm) rig.arm.rotation.x = rig.armX;
      } else {
        const running = motion === 'run';
        const phase = state.clock.elapsedTime * (running ? 11 : 5.6);
        const stride = Math.sin(phase) * (running ? 0.62 : 0.34);
        if (rig.leftLeg && rig.rightLeg) {
          rig.leftLeg.rotation.x = rig.leftLegX + stride;
          rig.rightLeg.rotation.x = rig.rightLegX - stride;
        }
        if (rig.leftArm && rig.arm) {
          rig.leftArm.rotation.x = rig.leftArmX - stride * 0.7;
          rig.arm.rotation.x = rig.armX + stride * 0.7;
        }
      }
    }
  });

  return <group ref={anchor} visible={visible} position={[0.95, -0.075, 1.15]} rotation={[0, -0.25, 0]}>
    {showDragHint && !lookHint && <Html position={[1.05, 0.62, 0]} center zIndexRange={[25, 0]}>
      <span className="avatar-drag-hint" aria-label="拖动鼠标转动人物"><span>拖动鼠标</span><span>转动人物</span></span>
    </Html>}
    {lookHint && <Html position={[lookHint.side < 0 ? -0.72 : 0.72, 0.78, 0]} center zIndexRange={[30, 0]}>
      <button type="button" className="avatar-look-hint" onPointerDown={(event) => event.stopPropagation()} onClick={(event) => { event.stopPropagation(); onLookAtDoor?.(lookHint); }}>
        {lookingDoorId === lookHint.id ? '向前看' : lookHint.side < 0 ? '向左看' : '向右看'}
      </button>
    </Html>}
    <group ref={turntable} scale={modelFit.scale} onPointerDown={beginDrag} onPointerUp={endDrag} onPointerCancel={endDrag} onPointerOver={() => { document.body.style.cursor = 'grab'; }} onPointerOut={() => { if (!drag.current) document.body.style.cursor = 'auto'; }}>
      <mesh position={modelFit.hitCenter} onPointerDown={beginDrag} onPointerUp={endDrag} onPointerCancel={endDrag}>
        <boxGeometry args={modelFit.hitSize} />
        <meshBasicMaterial transparent opacity={0} colorWrite={false} depthWrite={false} />
      </mesh>
      <primitive object={model} position={[0, modelFit.footOffset, 0]} />
    </group>
  </group>;
}

useGLTF.preload(MODEL_URL);
