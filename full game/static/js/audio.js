// ===== GLOBAL MUSIC CONTROLLER =====
const MUSIC_KEY = "escapex_musicToggle";
const MUSIC_TIME_KEY = "escapex_musicTime";

const bgMusic = document.getElementById("bgMusic");

if (bgMusic) {

  // restore position
  const savedTime = localStorage.getItem(MUSIC_TIME_KEY);
  if (savedTime) {
    bgMusic.currentTime = parseFloat(savedTime);
  }

  // auto play if enabled
  if (localStorage.getItem(MUSIC_KEY) === "true") {
    bgMusic.play().catch(()=>{});
  }

  // save position
  setInterval(() => {
    if (!bgMusic.paused) {
      localStorage.setItem(MUSIC_TIME_KEY, bgMusic.currentTime);
    }
  }, 1000);
}
