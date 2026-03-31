import * as THREE from 'three';

// Configurar escena, cámara y renderizador
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('bg-canvas'), alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

// Geometría de torus nudos (efecto tecnológico)
const geometry = new THREE.TorusKnotGeometry(1, 0.3, 100, 16);
const material = new THREE.MeshStandardMaterial({ color: 0x00ff9d, roughness: 0.3, metalness: 0.7, emissive: 0x00ff9d, emissiveIntensity: 0.2 });
const knot = new THREE.Mesh(geometry, material);
scene.add(knot);

// Añadir partículas alrededor
const particlesGeometry = new THREE.BufferGeometry();
const particlesCount = 2000;
const posArray = new Float32Array(particlesCount * 3);
for (let i = 0; i < particlesCount; i++) {
  posArray[i*3] = (Math.random() - 0.5) * 20;
  posArray[i*3+1] = (Math.random() - 0.5) * 20;
  posArray[i*3+2] = (Math.random() - 0.5) * 10;
}
particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
const particlesMaterial = new THREE.PointsMaterial({ color: 0x00ff9d, size: 0.05, transparent: true, opacity: 0.5 });
const particles = new THREE.Points(particlesGeometry, particlesMaterial);
scene.add(particles);

// Luz
const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);
const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
directionalLight.position.set(1, 1, 1);
scene.add(directionalLight);
const backLight = new THREE.PointLight(0x00ff9d, 0.3);
backLight.position.set(0, 0, 2);
scene.add(backLight);

camera.position.z = 5;

// Animación
function animate() {
  requestAnimationFrame(animate);
  knot.rotation.x += 0.005;
  knot.rotation.y += 0.01;
  particles.rotation.y += 0.001;
  renderer.render(scene, camera);
}
animate();

// Ajustar al resize de ventana
window.addEventListener('resize', onWindowResize, false);
function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}
