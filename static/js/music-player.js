class MusicPlayer {
  constructor() {
    this.currentTrackIndex = 0;
    this.tracks = [];
    this.audio = new Audio();
    this.isPlaying = false;
    
    this.init();
  }

  init() {
    this.injectHTML();
    this.cacheDOM();
    this.bindEvents();
    this.searchMusic('lofi chill'); // Default search
  }

  injectHTML() {
    const html = `
      <!-- Floating Action Button -->
      <button class="music-fab" id="musicFab" aria-label="Open Music Player">
        🎵
      </button>

      <!-- Player Card -->
      <div class="music-player-card" id="musicCard">
        <div class="music-header">
          <div class="music-search-container">
            <span class="music-search-icon">🔍</span>
            <input type="text" class="music-search-input" id="musicSearch" placeholder="Search for songs, artists..." autocomplete="off">
          </div>
        </div>

        <div class="music-yt-container" id="musicYtContainer" style="display: none;">
          <iframe id="musicYtIframe" width="100%" height="180" src="" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border-bottom: 1px solid rgba(255, 255, 255, 0.1);"></iframe>
        </div>

        <div class="music-loading" id="musicLoading">
          <div class="music-loading-spinner"></div>
          <div>Discovering tracks...</div>
        </div>

        <div class="music-track-list" id="musicTrackList"></div>

        <div class="music-now-playing">
          <div class="music-current-info">
            <img src="https://via.placeholder.com/150" alt="Album Art" class="music-current-art" id="currentArt">
            <div class="music-current-details">
              <div class="music-current-title" id="currentTitle">Select a track</div>
              <div class="music-current-artist" id="currentArtist">Search to begin</div>
            </div>
          </div>

          <div class="music-controls">
            <button class="music-btn" id="btnPrev" aria-label="Previous">⏮</button>
            <button class="music-btn music-btn-play" id="btnPlay" aria-label="Play/Pause">▶</button>
            <button class="music-btn" id="btnNext" aria-label="Next">⏭</button>
          </div>

          <div class="music-progress-container">
            <span class="music-time" id="timeCurrent">0:00</span>
            <div class="music-progress-bar" id="progressBar">
              <div class="music-progress-fill" id="progressFill"></div>
            </div>
            <span class="music-time" id="timeTotal">0:30</span>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', html);
  }

  cacheDOM() {
    this.fab = document.getElementById('musicFab');
    this.card = document.getElementById('musicCard');
    this.searchInput = document.getElementById('musicSearch');
    this.trackList = document.getElementById('musicTrackList');
    this.loading = document.getElementById('musicLoading');
    
    this.currentArt = document.getElementById('currentArt');
    this.currentTitle = document.getElementById('currentTitle');
    this.currentArtist = document.getElementById('currentArtist');
    
    this.ytContainer = document.getElementById('musicYtContainer');
    this.ytIframe = document.getElementById('musicYtIframe');
    
    this.btnPlay = document.getElementById('btnPlay');
    this.btnPrev = document.getElementById('btnPrev');
    this.btnNext = document.getElementById('btnNext');
    
    this.progressBar = document.getElementById('progressBar');
    this.progressFill = document.getElementById('progressFill');
    this.timeCurrent = document.getElementById('timeCurrent');
    this.timeTotal = document.getElementById('timeTotal');
  }

  bindEvents() {
    // Toggle Player
    this.fab.addEventListener('click', () => {
      this.card.classList.toggle('active');
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (!this.card.contains(e.target) && !this.fab.contains(e.target) && this.card.classList.contains('active')) {
        this.card.classList.remove('active');
      }
    });

    // Search
    let timeout = null;
    this.searchInput.addEventListener('input', (e) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        const query = e.target.value.trim();
        if (query.length > 0) {
          this.searchMusic(query);
        }
      }, 500);
    });

    // Controls
    this.btnPlay.addEventListener('click', () => this.togglePlay());
    this.btnPrev.addEventListener('click', () => this.playPrev());
    this.btnNext.addEventListener('click', () => this.playNext());

    // Audio Events
    this.audio.addEventListener('timeupdate', () => this.updateProgress());
    this.audio.addEventListener('ended', () => this.playNext());
    
    // Progress Bar Click
    this.progressBar.addEventListener('click', (e) => {
      if (!this.audio.src) return;
      const rect = this.progressBar.getBoundingClientRect();
      const percent = (e.clientX - rect.left) / rect.width;
      this.audio.currentTime = percent * this.audio.duration;
    });
  }

  async searchMusic(query) {
    this.trackList.innerHTML = '';
    this.loading.style.display = 'block';
    
    try {
      const response = await fetch(`https://itunes.apple.com/search?term=${encodeURIComponent(query)}&media=music&limit=25`);
      const data = await response.json();
      
      this.tracks = data.results.filter(t => t.previewUrl); // Ensure we have audio
      this.loading.style.display = 'none';
      this.renderTrackList();
      
      if (this.tracks.length > 0 && !this.isPlaying) {
        this.loadTrack(0);
      }
      
      // Load YouTube Video for the searched query
      this.loadYouTubeVideo(query);
      
    } catch (error) {
      console.error('Error fetching music:', error);
      this.loading.innerHTML = 'Error loading tracks. Try again later.';
    }
  }

  renderTrackList() {
    this.trackList.innerHTML = '';
    
    this.tracks.forEach((track, index) => {
      const item = document.createElement('div');
      item.className = `music-track-item ${index === this.currentTrackIndex ? 'playing' : ''}`;
      
      const artUrl = track.artworkUrl100 || 'https://via.placeholder.com/100';
      
      item.innerHTML = `
        <img src="${artUrl}" alt="Art" class="music-track-art">
        <div class="music-track-info">
          <div class="music-track-title">${track.trackName}</div>
          <div class="music-track-artist">${track.artistName}</div>
        </div>
      `;
      
      item.addEventListener('click', () => {
        this.loadTrack(index);
        this.play();
      });
      
      this.trackList.appendChild(item);
    });
  }

  loadTrack(index) {
    if (index < 0 || index >= this.tracks.length) return;
    
    this.currentTrackIndex = index;
    const track = this.tracks[index];
    
    this.audio.src = track.previewUrl;
    this.currentTitle.textContent = track.trackName;
    this.currentArtist.textContent = track.artistName;
    this.currentArt.src = track.artworkUrl100 ? track.artworkUrl100.replace('100x100bb', '600x600bb') : 'https://via.placeholder.com/600';
    
    // Update track list UI
    document.querySelectorAll('.music-track-item').forEach((item, i) => {
      if (i === index) item.classList.add('playing');
      else item.classList.remove('playing');
    });
    
    // Reset progress
    this.progressFill.style.width = '0%';
    this.timeCurrent.textContent = '0:00';
  }

  async fetchYoutubeVideoId(query) {
    const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
    
    // 1. Try Corsproxy.io (Very fast)
    try {
      const res = await fetch(`https://corsproxy.io/?${encodeURIComponent(searchUrl)}`);
      if (res.ok) {
        const text = await res.text();
        const match = text.match(/videoRenderer":\{"videoId":"([^"]+)"/);
        if (match) return match[1];
      }
    } catch (e) { }

    // 2. Fallback to scraping via Codetabs proxy
    try {
      const res = await fetch(`https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(searchUrl)}`);
      if (res.ok) {
        const text = await res.text();
        const match = text.match(/videoRenderer":\{"videoId":"([^"]+)"/);
        if (match) return match[1];
      }
    } catch (e) { }

    // 3. Fallback to AllOrigins proxy
    try {
      const res = await fetch(`https://api.allorigins.win/get?url=${encodeURIComponent(searchUrl)}`);
      if (res.ok) {
        const data = await res.json();
        const match = data.contents.match(/videoRenderer":\{"videoId":"([^"]+)"/);
        if (match) return match[1];
      }
    } catch (e) { }

    // 4. Try free Piped APIs as a last resort
    const instances = [
      'https://pipedapi.kavin.rocks',
      'https://pipedapi.smnz.de'
    ];
    for (let instance of instances) {
      try {
        const res = await fetch(`${instance}/search?q=${encodeURIComponent(query)}&filter=all`);
        if (!res.ok) continue;
        const data = await res.json();
        const video = data.items.find(item => item.type === 'stream');
        if (video && video.url) {
          return video.url.split('?v=')[1];
        }
      } catch (e) { }
    }
    
    return null;
  }

  async loadYouTubeVideo(query) {
    try {
      this.ytContainer.style.display = 'block';
      this.ytIframe.style.opacity = '0';
      this.ytIframe.style.transition = 'opacity 0.5s ease';
      
      const videoId = await this.fetchYoutubeVideoId(query);
      
      if (videoId) {
        this.ytIframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=0&rel=0`;
      } else {
        // Fallback to native YouTube search embed if scraping fails
        this.ytIframe.src = `https://www.youtube.com/embed?listType=search&list=${encodeURIComponent(query)}`;
      }
      
      this.ytIframe.onload = () => {
        this.ytIframe.style.opacity = '1';
      };
    } catch (err) {
      console.error('Error fetching YouTube video:', err);
      this.ytContainer.style.display = 'none';
    }
  }

  togglePlay() {
    if (!this.audio.src) return;
    
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }
  }

  play() {
    this.audio.play();
    this.isPlaying = true;
    this.btnPlay.textContent = '⏸';
    this.currentArt.classList.add('spinning');
  }

  pause() {
    this.audio.pause();
    this.isPlaying = false;
    this.btnPlay.textContent = '▶';
    this.currentArt.classList.remove('spinning');
  }

  playNext() {
    let nextIndex = this.currentTrackIndex + 1;
    if (nextIndex >= this.tracks.length) nextIndex = 0; // Loop back
    this.loadTrack(nextIndex);
    this.play();
  }

  playPrev() {
    let prevIndex = this.currentTrackIndex - 1;
    if (prevIndex < 0) prevIndex = this.tracks.length - 1;
    this.loadTrack(prevIndex);
    this.play();
  }

  updateProgress() {
    const { currentTime, duration } = this.audio;
    if (isNaN(duration)) return;
    
    const percent = (currentTime / duration) * 100;
    this.progressFill.style.width = `${percent}%`;
    
    this.timeCurrent.textContent = this.formatTime(currentTime);
  }

  formatTime(seconds) {
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new MusicPlayer();
});
