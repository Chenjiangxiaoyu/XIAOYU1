<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import type { TeachingStep } from '@/types/domain'
import type { PoseSequence } from '@/modules/pose/PoseTypes'
import { PoseRetargeter } from '@/modules/teaching/PoseRetargeter'

const props = defineProps<{ step: TeachingStep; playing: boolean; referenceSequence: PoseSequence | null }>()
const host = ref<HTMLDivElement>()
let renderer: THREE.WebGLRenderer | undefined
let scene: THREE.Scene | undefined
let camera: THREE.PerspectiveCamera | undefined
let frameId = 0
let startedAt = performance.now()
const limbs: Record<string, THREE.Object3D> = {}
const retargeter = new PoseRetargeter()

function limb(length: number, color: number) {
  const group = new THREE.Group()
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.09, length, 12), new THREE.MeshStandardMaterial({ color, roughness: 0.65 }))
  mesh.position.y = -length / 2
  group.add(mesh)
  return group
}

function resize() {
  if (!host.value || !renderer || !camera) return
  const { clientWidth: width, clientHeight: height } = host.value
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function animate(now: number) {
  if (!renderer || !scene || !camera) return
  const phase = props.playing ? (now - startedAt) / 320 : 0
  const pose = retargeter.poseAt(props.referenceSequence, props.step, phase / 3.125)
  limbs.leftArm.rotation.z = pose.leftArm
  limbs.rightArm.rotation.z = pose.rightArm
  limbs.leftLeg.rotation.z = pose.leftLeg
  limbs.rightLeg.rotation.z = pose.rightLeg
  limbs.torso.rotation.z = pose.torso
  scene.rotation.y = Math.sin(phase * 0.18) * 0.12
  renderer.render(scene, camera)
  frameId = requestAnimationFrame(animate)
}

onMounted(() => {
  if (!host.value) return
  scene = new THREE.Scene()
  scene.background = new THREE.Color('#eff6ff')
  camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100)
  camera.position.set(0, 1.8, 5.5)
  camera.lookAt(0, 1.4, 0)
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  host.value.appendChild(renderer.domElement)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x1e3a8a, 2.3))
  const ground = new THREE.Mesh(new THREE.CircleGeometry(1.75, 40), new THREE.MeshStandardMaterial({ color: 0xdbeafe, roughness: 1 }))
  ground.rotation.x = -Math.PI / 2
  scene.add(ground)
  const body = new THREE.Group()
  const blue = 0x2563eb
  const torso = new THREE.Mesh(new THREE.CapsuleGeometry(0.34, 0.78, 8, 16), new THREE.MeshStandardMaterial({ color: blue, roughness: 0.55 }))
  torso.position.y = 1.72
  body.add(torso)
  limbs.torso = torso
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.25, 16, 16), new THREE.MeshStandardMaterial({ color: 0xf1c7a5, roughness: 0.7 }))
  head.position.y = 2.43
  body.add(head)
  for (const [name, x, y, length] of [['leftArm', -0.37, 2.05, 0.78], ['rightArm', 0.37, 2.05, 0.78], ['leftLeg', -0.2, 1.25, 0.95], ['rightLeg', 0.2, 1.25, 0.95]] as const) {
    const part = limb(length, name.includes('Arm') ? 0x60a5fa : 0x1d4ed8)
    part.position.set(x, y, 0)
    body.add(part)
    limbs[name] = part
  }
  scene.add(body)
  resize()
  window.addEventListener('resize', resize)
  frameId = requestAnimationFrame(animate)
})

watch(() => props.step.id, () => { startedAt = performance.now() })
onBeforeUnmount(() => { cancelAnimationFrame(frameId); window.removeEventListener('resize', resize); renderer?.dispose() })
</script>

<template><div ref="host" class="avatar-preview" aria-label="3D 动作示范预览" /></template>

<style scoped>.avatar-preview { width: 100%; height: 320px; overflow: hidden; border-radius: 8px; }</style>
