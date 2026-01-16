"""Web-based dashboard UI for Flowstate."""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, render_template_string, jsonify, request

from ..models import Corpus, Track, Recommendations
from ..engine import RecommendationEngine

# HTML template embedded in Python for simplicity
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FLOWSTATE</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .logo { font-size: 24px; font-weight: bold; color: #00d4ff; }
        .status { display: flex; gap: 20px; align-items: center; }
        .status-item { font-size: 14px; color: #888; }
        .rb-connected { color: #4ade80; }
        .rb-disconnected { color: #666; }

        /* Main grid - new layout with tracks on top, recs below */
        .main-grid {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .tracks-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .left-col { display: contents; } /* Remove wrapper behavior */

        /* Now Playing */
        .now-playing {
            background: rgba(0,212,255,0.1);
            border: 1px solid rgba(0,212,255,0.3);
            border-radius: 10px;
            padding: 20px;
        }
        .now-playing h2 { color: #00d4ff; font-size: 14px; margin-bottom: 15px; }
        .track-title { font-size: 24px; font-weight: bold; margin-bottom: 5px; }
        .track-artist { font-size: 18px; color: #00d4ff; margin-bottom: 15px; }
        .track-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        .stat { text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #ffd700; }
        .stat-label { font-size: 12px; color: #888; }
        .energy-bar {
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }
        .energy-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ffd700, #4ade80);
            transition: width 0.3s;
        }
        .track-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        .tag {
            padding: 4px 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            font-size: 12px;
        }
        .tag.vibe { background: rgba(255,0,255,0.2); color: #ff66ff; }
        .tag.intensity { background: rgba(255,215,0,0.2); color: #ffd700; }

        /* Analysis */
        .analysis {
            background: rgba(100,100,255,0.1);
            border: 1px solid rgba(100,100,255,0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        .analysis h2 { color: #6b7fff; font-size: 14px; margin-bottom: 15px; }
        .analysis-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .analysis-item label { font-size: 12px; color: #888; display: block; }
        .analysis-item span { font-size: 14px; }
        .description {
            grid-column: 1 / -1;
            font-style: italic;
            color: #aaa;
            margin-top: 10px;
            line-height: 1.5;
        }

        /* Track Preview / Candidate - side by side with Now Playing */
        .up-next {
            background: rgba(74,222,128,0.1);
            border: 2px solid rgba(74,222,128,0.4);
            border-radius: 10px;
            padding: 20px;
        }
        .up-next:not(.active) {
            border-color: rgba(100,100,100,0.3);
            background: rgba(50,50,50,0.2);
        }
        .up-next:not(.active) h2 { color: #666; }
        .up-next h2 { color: #4ade80; font-size: 14px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        .up-next .track-title { font-size: 20px; }
        .up-next .track-artist { font-size: 16px; color: #4ade80; }
        .up-next-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .up-next-btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.2s;
        }
        .up-next-btn.confirm {
            background: #4ade80;
            color: #000;
        }
        .up-next-btn.confirm:hover { background: #22c55e; }
        .up-next-btn.cancel {
            background: rgba(255,255,255,0.1);
            color: #888;
        }
        .up-next-btn.cancel:hover { background: rgba(255,255,255,0.2); }
        .transition-info {
            display: flex;
            gap: 20px;
            margin: 15px 0;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }
        .transition-stat {
            text-align: center;
        }
        .transition-stat .value {
            font-size: 18px;
            font-weight: bold;
        }
        .transition-stat .label {
            font-size: 11px;
            color: #888;
        }
        .transition-stat .delta {
            font-size: 12px;
        }
        .transition-stat .delta.positive { color: #4ade80; }
        .transition-stat .delta.negative { color: #ff6b6b; }
        .transition-stat .delta.neutral { color: #ffd700; }

        /* Recommendations - horizontal row below tracks */
        .recommendations {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }
        .rec-panel {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            flex: 1;
        }
        .rec-panel.up { border-left: 3px solid #4ade80; }
        .rec-panel.hold { border-left: 3px solid #ffd700; }
        .rec-panel.down { border-left: 3px solid #ff6b6b; }
        .rec-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .rec-title { font-weight: bold; }
        .rec-title.up { color: #4ade80; }
        .rec-title.hold { color: #ffd700; }
        .rec-title.down { color: #ff6b6b; }
        .rec-count { font-size: 12px; color: #666; }

        .rec-list { list-style: none; }
        .rec-item {
            display: grid;
            grid-template-columns: 30px 1fr auto auto auto auto;
            gap: 10px;
            align-items: center;
            padding: 8px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .rec-item:hover { background: rgba(255,255,255,0.1); }
        .rec-num { color: #666; font-weight: bold; }
        .rec-track-info { overflow: hidden; }
        .rec-track-title { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .rec-track-artist { font-size: 12px; color: #888; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .rec-bpm, .rec-key { font-size: 12px; color: #888; min-width: 35px; text-align: right; }
        .rec-energy { font-size: 14px; font-weight: bold; min-width: 20px; text-align: center; }
        .rec-energy.up { color: #4ade80; }
        .rec-energy.down { color: #ff6b6b; }
        .rec-energy.same { color: #ffd700; }
        .rec-score { font-size: 12px; color: #666; min-width: 40px; text-align: right; }

        /* Search */
        .search-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .search-input {
            flex: 1;
            padding: 12px 20px;
            border: 1px solid #333;
            border-radius: 25px;
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 16px;
        }
        .search-input:focus { outline: none; border-color: #00d4ff; }
        .search-btn {
            padding: 12px 25px;
            background: #00d4ff;
            color: #000;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
        }
        .search-btn:hover { background: #00b8e6; }

        /* Search Results Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: #1a1a2e;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .modal-close {
            background: none;
            border: none;
            color: #888;
            font-size: 24px;
            cursor: pointer;
        }
        .search-results { list-style: none; }
        .search-result {
            padding: 15px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
            display: grid;
            grid-template-columns: 1fr auto auto auto;
            gap: 15px;
            align-items: center;
        }
        .search-result:hover { background: rgba(0,212,255,0.1); }

        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .empty-state h3 { margin-bottom: 10px; }

        /* Keyboard hints */
        .keyboard-hints {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 12px;
            color: #666;
        }
        .keyboard-hints kbd {
            background: #333;
            padding: 2px 8px;
            border-radius: 3px;
            margin: 0 2px;
        }
        .rb-indicator {
            font-size: 10px;
            color: #888;
            margin-top: 5px;
        }
        .rb-refresh-btn {
            background: none;
            border: 1px solid #444;
            color: #888;
            padding: 4px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        .rb-refresh-btn:hover {
            background: rgba(0,212,255,0.2);
            border-color: #00d4ff;
            color: #00d4ff;
        }
        .rb-refresh-btn.loading {
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">FLOWSTATE</div>
            <div class="status">
                <span class="status-item" id="rb-status">
                    <span class="rb-disconnected">○</span> Rekordbox
                </span>
                <button class="rb-refresh-btn" onclick="refreshRekordbox()" title="Refresh Rekordbox">⟳</button>
                <span class="status-item" id="set-info"></span>
                <span class="status-item" id="clock"></span>
            </div>
        </div>

        <div class="search-bar">
            <input type="text" class="search-input" id="search-input" placeholder="Search tracks..." />
            <button class="search-btn" onclick="openSearch()">Search</button>
        </div>

        <div class="main-grid">
            <!-- Top row: Now Playing and Track Preview side by side -->
            <div class="tracks-row">
                <div class="now-playing" id="now-playing">
                    <h2>NOW PLAYING</h2>
                    <div class="empty-state">
                        <h3>Waiting for Rekordbox</h3>
                        <p>Play a track in Rekordbox to get started</p>
                        <div class="rb-indicator">Now Playing is synced from Rekordbox</div>
                    </div>
                </div>

                <div class="up-next" id="up-next">
                    <h2>
                        <span>TRACK PREVIEW</span>
                        <span style="font-size:12px;font-weight:normal;color:#888;" id="up-next-score"></span>
                    </h2>
                    <div id="up-next-content">
                        <div class="empty-state" style="padding:20px;">
                            <p style="color:#666;">Click a recommendation to preview</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Bottom row: Recommendations -->
            <div class="recommendations">
                <div class="rec-panel up">
                    <div class="rec-header">
                        <span class="rec-title up">↑ UP</span>
                        <span class="rec-count" id="up-count">0 matches</span>
                    </div>
                    <ul class="rec-list" id="up-list"></ul>
                </div>

                <div class="rec-panel hold">
                    <div class="rec-header">
                        <span class="rec-title hold">→ HOLD</span>
                        <span class="rec-count" id="hold-count">0 matches</span>
                    </div>
                    <ul class="rec-list" id="hold-list"></ul>
                </div>

                <div class="rec-panel down">
                    <div class="rec-header">
                        <span class="rec-title down">↓ DOWN</span>
                        <span class="rec-count" id="down-count">0 matches</span>
                    </div>
                    <ul class="rec-list" id="down-list"></ul>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="search-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Search Results</h2>
                <button class="modal-close" onclick="closeSearch()">&times;</button>
            </div>
            <ul class="search-results" id="search-results"></ul>
        </div>
    </div>

    <div class="keyboard-hints">
        <kbd>S</kbd> Search &nbsp;
        <kbd>1-5</kbd> Preview UP &nbsp;
        <kbd>U/H/D</kbd>+<kbd>1-5</kbd> Preview &nbsp;
        <kbd>Esc</kbd> Close Preview &nbsp;
        <kbd>R</kbd> Refresh RB
    </div>

    <script>
        let currentTrack = null;
        let currentEnergy = 5;
        let setStartTime = null;
        let trackCount = 0;
        let candidateTrack = null;
        let currentRecommendations = null;

        // Update clock
        setInterval(() => {
            document.getElementById('clock').textContent = new Date().toLocaleTimeString();
            if (setStartTime) {
                const elapsed = Math.floor((Date.now() - setStartTime) / 60000);
                document.getElementById('set-info').textContent = `Set: ${elapsed}min | ${trackCount} tracks`;
            }
        }, 1000);

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;

            if (e.key === 's' || e.key === 'S') {
                openSearch();
            } else if (e.key === 'r' || e.key === 'R') {
                refreshRekordbox();
            } else if (e.key >= '1' && e.key <= '5') {
                selectFromList('up', parseInt(e.key) - 1);
            } else if (e.key === 'u' || e.key === 'U') {
                waitForNumber('up');
            } else if (e.key === 'h' || e.key === 'H') {
                waitForNumber('hold');
            } else if (e.key === 'd' || e.key === 'D') {
                waitForNumber('down');
            } else if (e.key === 'Escape') {
                if (candidateTrack) clearCandidate();
                else closeSearch();
            }
        });

        let pendingDirection = null;
        function waitForNumber(direction) {
            pendingDirection = direction;
            setTimeout(() => { pendingDirection = null; }, 2000);
        }

        document.addEventListener('keydown', (e) => {
            if (pendingDirection && e.key >= '1' && e.key <= '5') {
                selectFromList(pendingDirection, parseInt(e.key) - 1);
                pendingDirection = null;
            }
        });

        function selectFromList(direction, index) {
            const list = document.getElementById(`${direction}-list`);
            const items = list.querySelectorAll('.rec-item');
            if (items[index]) {
                const trackId = items[index].dataset.trackId;
                previewCandidate(trackId);
            }
        }

        async function previewCandidate(trackId) {
            const response = await fetch(`/api/track/${trackId}`);
            const track = await response.json();
            if (track) {
                candidateTrack = track;
                renderUpNext(track);
            }
        }

        function renderUpNext(track) {
            const container = document.getElementById('up-next');
            const content = document.getElementById('up-next-content');
            const scoreEl = document.getElementById('up-next-score');

            container.classList.add('active');

            // Calculate transition info
            const bpmDelta = currentTrack ? (track.bpm - currentTrack.bpm).toFixed(0) : 0;
            const energyDelta = currentTrack ? track.energy - currentTrack.energy : 0;
            const keyCompatible = currentTrack ? checkKeyCompatibility(currentTrack.key, track.key) : 'N/A';

            const bpmClass = Math.abs(bpmDelta) <= 3 ? 'neutral' : (bpmDelta > 0 ? 'positive' : 'negative');
            const energyClass = energyDelta > 0 ? 'positive' : (energyDelta < 0 ? 'negative' : 'neutral');

            content.innerHTML = `
                <div class="track-title">${track.title}</div>
                <div class="track-artist">${track.artist}</div>

                <div class="transition-info">
                    <div class="transition-stat">
                        <div class="value">${track.bpm.toFixed(0)}</div>
                        <div class="label">BPM</div>
                        <div class="delta ${bpmClass}">${bpmDelta > 0 ? '+' : ''}${bpmDelta}</div>
                    </div>
                    <div class="transition-stat">
                        <div class="value">${track.key}</div>
                        <div class="label">KEY</div>
                        <div class="delta ${keyCompatible === 'Perfect' || keyCompatible === 'Good' ? 'positive' : 'neutral'}">${keyCompatible}</div>
                    </div>
                    <div class="transition-stat">
                        <div class="value">${track.energy}</div>
                        <div class="label">ENERGY</div>
                        <div class="delta ${energyClass}">${energyDelta > 0 ? '+' : ''}${energyDelta}</div>
                    </div>
                    <div class="transition-stat">
                        <div class="value">${track.mix_in_ease}</div>
                        <div class="label">MIX IN</div>
                    </div>
                </div>

                <div class="track-tags">
                    <span class="tag vibe">${track.vibe}</span>
                    <span class="tag intensity">${track.intensity}</span>
                    <span class="tag">${track.groove_style}</span>
                </div>

                <div class="analysis-grid" style="margin-top:15px;">
                    <div class="analysis-item">
                        <label>Vocals</label>
                        <span>${track.vocal_presence} • ${track.vocal_style}</span>
                    </div>
                    <div class="analysis-item">
                        <label>Genre</label>
                        <span>${track.genre}${track.subgenre ? ' / ' + track.subgenre : ''}</span>
                    </div>
                    <div class="description">${track.description}</div>
                </div>

                <div class="up-next-actions">
                    <button class="up-next-btn cancel" onclick="clearCandidate()">✕ Close Preview</button>
                </div>
            `;
        }

        function checkKeyCompatibility(key1, key2) {
            // Simple Camelot compatibility check
            if (!key1 || !key2) return 'N/A';
            if (key1 === key2) return 'Perfect';

            // Extract number and letter
            const num1 = parseInt(key1);
            const letter1 = key1.slice(-1);
            const num2 = parseInt(key2);
            const letter2 = key2.slice(-1);

            // Same number, different letter (relative major/minor)
            if (num1 === num2 && letter1 !== letter2) return 'Perfect';

            // Adjacent numbers, same letter
            if (letter1 === letter2) {
                const diff = Math.abs(num1 - num2);
                if (diff === 1 || diff === 11) return 'Good';
            }

            // Energy boost (+1) or drop (-1)
            if (letter1 === letter2) {
                const diff = (num2 - num1 + 12) % 12;
                if (diff === 1 || diff === 11) return 'Good';
                if (diff === 2 || diff === 10) return 'OK';
            }

            return 'Risky';
        }

        function clearCandidate() {
            candidateTrack = null;
            document.getElementById('up-next').classList.remove('active');
            document.getElementById('up-next-content').innerHTML = `
                <div class="empty-state" style="padding:20px;">
                    <p style="color:#666;">Click a recommendation to preview</p>
                </div>
            `;
        }

        // Called only from Rekordbox sync - Now Playing is driven by Rekordbox
        async function syncFromRekordbox(trackId, force = false) {
            // Skip if already showing this track (unless forced)
            if (!force && currentTrack && currentTrack.track_id === trackId) {
                return;
            }

            console.log(`Rekordbox sync: ${trackId}${force ? ' (forced)' : ''}`);

            const response = await fetch(`/api/select/${trackId}`);
            const data = await response.json();

            if (data.error) {
                console.error('Error syncing track:', data.error);
                return;
            }

            if (data.track) {
                const isNewTrack = !currentTrack || currentTrack.track_id !== data.track.track_id;

                currentTrack = data.track;
                currentEnergy = data.track.energy;
                currentRecommendations = data.recommendations;

                if (!setStartTime) setStartTime = Date.now();
                if (isNewTrack) trackCount++;

                renderNowPlaying(data.track);
                renderAnalysis(data.track);
                renderRecommendations(data.recommendations);

                console.log(`Now playing (from Rekordbox): ${data.track.title} by ${data.track.artist}`);
            }
        }

        function renderNowPlaying(track) {
            const container = document.getElementById('now-playing');
            const energyPercent = track.energy * 10;

            container.innerHTML = `
                <h2>NOW PLAYING</h2>
                <div class="track-title">${track.title}</div>
                <div class="track-artist">${track.artist}</div>
                <div class="track-stats">
                    <div class="stat">
                        <div class="stat-value">${track.bpm.toFixed(0)}</div>
                        <div class="stat-label">BPM</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${track.key}</div>
                        <div class="stat-label">KEY</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${track.energy}</div>
                        <div class="stat-label">ENERGY</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">${track.mix_out_ease}</div>
                        <div class="stat-label">MIX OUT</div>
                    </div>
                </div>
                <div class="track-tags">
                    <span class="tag vibe">${track.vibe}</span>
                    <span class="tag intensity">${track.intensity}</span>
                    <span class="tag">${track.groove_style}</span>
                </div>
                <div style="margin-top:10px;font-size:12px;color:#888;font-style:italic;">${track.description}</div>
            `;
        }

        function renderAnalysis(track) {
            // No longer needed - analysis shown in Now Playing
        }

        function renderRecommendations(recs) {
            ['up', 'hold', 'down'].forEach(dir => {
                const list = document.getElementById(`${dir}-list`);
                const count = document.getElementById(`${dir}-count`);
                const tracks = recs[dir] || [];

                count.textContent = `${tracks.length} matches`;

                if (tracks.length === 0) {
                    list.innerHTML = '<li class="empty-state" style="padding:20px;"><small>No matches</small></li>';
                    return;
                }

                list.innerHTML = tracks.slice(0, 5).map((item, i) => {
                    const t = item.track;
                    const delta = t.energy - currentEnergy;
                    const energyClass = delta > 0 ? 'up' : delta < 0 ? 'down' : 'same';
                    return `
                        <li class="rec-item" data-track-id="${t.track_id}" onclick="previewCandidate('${t.track_id}')">
                            <span class="rec-num">${i + 1}</span>
                            <div class="rec-track-info">
                                <div class="rec-track-title">${t.title}</div>
                                <div class="rec-track-artist">${t.artist}</div>
                            </div>
                            <span class="rec-bpm">${t.bpm.toFixed(0)}</span>
                            <span class="rec-key">${t.key}</span>
                            <span class="rec-energy ${energyClass}">${t.energy}</span>
                            <span class="rec-score">${item.total_score.toFixed(2)}</span>
                        </li>
                    `;
                }).join('');
            });
        }

        async function openSearch() {
            const query = document.getElementById('search-input').value;
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();

            const container = document.getElementById('search-results');
            container.innerHTML = results.map(t => `
                <li class="search-result" onclick="previewCandidate('${t.track_id}'); closeSearch();">
                    <div>
                        <div style="font-weight:bold;">${t.title}</div>
                        <div style="color:#888;">${t.artist}</div>
                    </div>
                    <span>${t.bpm.toFixed(0)} BPM</span>
                    <span>${t.key}</span>
                    <span>E=${t.energy}</span>
                </li>
            `).join('');

            document.getElementById('search-modal').classList.add('active');
            document.getElementById('search-input').value = '';
        }

        function closeSearch() {
            document.getElementById('search-modal').classList.remove('active');
        }

        // Search on Enter
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') openSearch();
        });

        // Manual Rekordbox refresh - forces sync even if same track
        async function refreshRekordbox() {
            const btn = document.querySelector('.rb-refresh-btn');
            btn.classList.add('loading');
            await checkRekordbox(true);  // force=true
            btn.classList.remove('loading');
        }

        // Check Rekordbox status and auto-load
        async function checkRekordbox(force = false) {
            try {
                const response = await fetch('/api/rekordbox/now-playing');
                const data = await response.json();

                const statusEl = document.getElementById('rb-status');
                if (data.connected) {
                    if (data.rb_info && data.rb_info.not_in_corpus) {
                        statusEl.innerHTML = `<span class="rb-connected">●</span> RB: ${data.rb_info.artist} - ${data.rb_info.title} <span style="color:#ffd700">(not in corpus)</span>`;
                    } else if (data.track) {
                        statusEl.innerHTML = '<span class="rb-connected">●</span> Rekordbox';
                        syncFromRekordbox(data.track.track_id, force);
                    } else {
                        statusEl.innerHTML = '<span class="rb-connected">●</span> Rekordbox (no track)';
                    }
                } else {
                    statusEl.innerHTML = '<span class="rb-disconnected">○</span> Rekordbox' + (data.error ? `: ${data.error}` : '');
                }
            } catch (e) {
                console.error('Rekordbox check failed:', e);
            }
        }

        // Poll Rekordbox every 3 seconds
        setInterval(checkRekordbox, 3000);
        checkRekordbox();
    </script>
</body>
</html>
"""


class WebUI:
    """Web-based dashboard for Flowstate."""

    def __init__(self, corpus: Corpus, engine: RecommendationEngine, rekordbox_sync: bool = True):
        self.corpus = corpus
        self.engine = engine
        self.rekordbox_sync = rekordbox_sync
        self.app = Flask(__name__)
        self._rb_monitor = None
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)

        @self.app.route('/api/search')
        def search():
            query = request.args.get('q', '')
            if query:
                results = self.corpus.search(query)[:15]
            else:
                results = random.sample(self.corpus.tracks, min(15, len(self.corpus.tracks)))
            return jsonify([self._track_to_dict(t) for t in results])

        @self.app.route('/api/track/<track_id>')
        def get_track(track_id):
            track = self.corpus.get_by_id(track_id)
            if not track:
                return jsonify({'error': 'Track not found'}), 404
            return jsonify(self._track_to_dict(track))

        @self.app.route('/api/select/<track_id>')
        def select(track_id):
            track = self.corpus.get_by_id(track_id)
            if not track:
                return jsonify({'error': 'Track not found'}), 404

            recs = self.engine.recommend(track)
            return jsonify({
                'track': self._track_to_dict(track),
                'recommendations': {
                    'up': [{'track': self._track_to_dict(s.track), 'total_score': s.total_score} for s in recs.up[:5]],
                    'hold': [{'track': self._track_to_dict(s.track), 'total_score': s.total_score} for s in recs.hold[:5]],
                    'down': [{'track': self._track_to_dict(s.track), 'total_score': s.total_score} for s in recs.down[:5]],
                }
            })

        @self.app.route('/api/rekordbox/now-playing')
        def rekordbox_now_playing():
            if not self.rekordbox_sync:
                return jsonify({'connected': False})

            try:
                from ..integrations.rekordbox import RekordboxMonitor

                # Create monitor and check for track
                monitor = RekordboxMonitor(self.corpus)
                if not monitor._init_rekordbox():
                    return jsonify({'connected': False, 'error': 'Could not connect to Rekordbox DB'})

                try:
                    # Refresh DB to get latest history
                    monitor._refresh_db_copy()
                    rb_track = monitor._get_recent_track()

                    if rb_track:
                        matched = monitor._match_to_corpus(rb_track)
                        if matched:
                            return jsonify({
                                'connected': True,
                                'track': self._track_to_dict(matched),
                                'rb_info': {
                                    'title': rb_track.get('title'),
                                    'artist': rb_track.get('artist')
                                }
                            })
                        else:
                            # Track found in RB but not in corpus
                            return jsonify({
                                'connected': True,
                                'track': None,
                                'rb_info': {
                                    'title': rb_track.get('title'),
                                    'artist': rb_track.get('artist'),
                                    'not_in_corpus': True
                                }
                            })
                    return jsonify({'connected': True, 'track': None})
                finally:
                    monitor._cleanup()

            except Exception as e:
                import traceback
                return jsonify({'connected': False, 'error': str(e), 'trace': traceback.format_exc()})

        @self.app.route('/api/rekordbox/debug')
        def rekordbox_debug():
            """Debug endpoint showing raw Rekordbox data."""
            if not self.rekordbox_sync:
                return jsonify({'error': 'Rekordbox sync disabled'})

            try:
                from ..integrations.rekordbox import RekordboxMonitor

                monitor = RekordboxMonitor(self.corpus)
                if not monitor._init_rekordbox():
                    return jsonify({'error': 'Could not init Rekordbox'})

                try:
                    # Get all recent history entries
                    history_info = []
                    history = list(monitor._rb.get_history())
                    for h in history[-3:]:  # Last 3 history entries
                        songs = []
                        for song in list(h.Songs)[-5:]:  # Last 5 songs each
                            content = song.Content
                            if content:
                                songs.append({
                                    'title': content.Title,
                                    'artist': content.ArtistName,
                                    'id': str(content.ID)
                                })
                        history_info.append({
                            'name': str(h.Name) if hasattr(h, 'Name') else 'unknown',
                            'songs': songs
                        })

                    rb_track = monitor._get_recent_track()
                    matched = monitor._match_to_corpus(rb_track) if rb_track else None

                    return jsonify({
                        'history': history_info,
                        'latest_rb_track': rb_track,
                        'matched_corpus_track': matched.title if matched else None,
                        'corpus_size': len(self.corpus.tracks)
                    })
                finally:
                    monitor._cleanup()

            except Exception as e:
                import traceback
                return jsonify({'error': str(e), 'trace': traceback.format_exc()})

    def _track_to_dict(self, track: Track) -> dict:
        """Convert Track to JSON-serializable dict."""
        return {
            'track_id': track.track_id,
            'title': track.title,
            'artist': track.artist,
            'bpm': track.bpm,
            'key': track.key,
            'duration_seconds': track.duration_seconds,
            'energy': track.energy,
            'danceability': track.danceability,
            'vibe': track.vibe if isinstance(track.vibe, str) else track.vibe.value,
            'intensity': track.intensity if isinstance(track.intensity, str) else track.intensity.value,
            'mood_tags': track.mood_tags,
            'groove_style': track.groove_style if isinstance(track.groove_style, str) else track.groove_style.value,
            'tempo_feel': track.tempo_feel,
            'mix_in_ease': track.mix_in_ease,
            'mix_out_ease': track.mix_out_ease,
            'mixability_notes': track.mixability_notes,
            'vocal_presence': track.vocal_presence if isinstance(track.vocal_presence, str) else track.vocal_presence.value,
            'vocal_style': track.vocal_style if isinstance(track.vocal_style, str) else track.vocal_style.value,
            'structure': track.structure,
            'drop_intensity': track.drop_intensity,
            'genre': track.genre,
            'subgenre': track.subgenre,
            'description': track.description,
        }

    def run(self, host: str = '0.0.0.0', port: int = 5000):
        """Run the web server."""
        print(f"\n  FLOWSTATE Web UI")
        print(f"  Open http://localhost:{port} in your browser\n")
        self.app.run(host=host, port=port, debug=False)
