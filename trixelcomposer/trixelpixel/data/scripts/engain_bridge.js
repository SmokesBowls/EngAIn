// EngAIn ZW Bridge for TrixelPixel -- ES5 compatible
// Rewritten for LibreSprite's older JS engine: no let/const, no arrows,
// no template literals, no Object.entries/assign, no destructuring, no spread.
// Behavior identical to original.
//
// Endpoints (mirrors empire_bridge.py defaults):
//   Ollama:        http://localhost:11434   (local LLM, primary)
//   Empire broker: http://localhost:5010    (ZW orchestration, secondary)
//   Scene server:  http://localhost:8090    (scene context / ZW intent)

var BRIDGE_VERSION = "0.1";

var defaultSettings = {
    mode:            "ollama",
    ollamaEndpoint:  "http://localhost:11434",
    empireEndpoint:  "http://localhost:5010",
    sceneEndpoint:   "http://127.0.0.1:8765/load_scene?scene_id=scene.002_molten_descent",
    recipeEndpoint:  "http://127.0.0.1:8765/art_recipe?scene_id=002_molten_descent",
    model:           "llama3.2:3b",
    artIntent:       "pixel art sprite, EngAIn fantasy world",
    sessionId:       "",
    autoApply:       "0",
    iterations:      "5"
};

// ---------------------------------------------------------------------------
// HTTP helpers -- same callback pattern as ai.js
// storage.fetch() fires onEvent(key + "_fetch") when the response arrives,
// which routes through onEvent -> engain[key + "_fetch"]().
// ---------------------------------------------------------------------------

function post(url, body, cb) {
    var key = engain.nextId++ + 'e';
    engain[key + '_fetch'] = function() {
        var status = storage.get(key + '_status');
        var text   = storage.get(key);
        delete engain[key + '_fetch'];
        cb({ text: text, status: status });
    };
    storage.fetch(url, key, "", "POST", body, "Content-Type", "application/json");
}

function httpGet(url, cb) {
    var key = engain.nextId++ + 'e';
    engain[key + '_fetch'] = function() {
        var status = storage.get(key + '_status');
        var text   = storage.get(key);
        delete engain[key + '_fetch'];
        cb({ text: text, status: status });
    };
    storage.fetch(url, key, "");
}

function postJSON(url, payload, cb) {
    post(url, JSON.stringify(payload), function(rsp) {
        if (rsp.status !== 200) { cb(null, 'HTTP ' + rsp.status); return; }
        try   { cb(JSON.parse(rsp.text), null); }
        catch (ex) { cb(null, 'parse error: ' + ex + '\n' + (rsp.text || '').substring(0, 200)); }
    });
}

// ---------------------------------------------------------------------------
// Canvas helpers
// ---------------------------------------------------------------------------

function getCanvasInfo() {
    var sprite, layerNum, cel, img, w, h, data;
    var i, bkey, painted, pct;
    var buckets, bucketArr, bk, topColors, ti, v;

    sprite = app.activeSprite;
    if (!sprite) { return null; }
    layerNum = app.activeLayerNumber;
    cel = sprite.layer(layerNum).cel(0);
    if (!cel) { return null; }
    img  = cel.image;
    w    = img.width;
    h    = img.height;
    data = img.getImageData();

    painted = 0;
    buckets = {};
    for (i = 0; i < data.length; i += 4) {
        if (data[i + 3] > 0) {
            painted++;
            bkey = ((data[i] >> 5) << 6) | ((data[i + 1] >> 5) << 3) | (data[i + 2] >> 5);
            buckets[bkey] = (buckets[bkey] || 0) + 1;
        }
    }
    pct = ((painted / (w * h)) * 100) | 0;

    // Sort buckets by frequency, take top 3
    bucketArr = [];
    for (bk in buckets) {
        if (buckets.hasOwnProperty(bk)) {
            bucketArr.push([bk, buckets[bk]]);
        }
    }
    bucketArr.sort(function(a, b) { return b[1] - a[1]; });

    topColors = [];
    for (ti = 0; ti < 3 && ti < bucketArr.length; ti++) {
        v = +bucketArr[ti][0];
        topColors.push('rgb(' + ((v >> 6) << 5) + ',' + (((v >> 3) & 7) << 5) + ',' + ((v & 7) << 5) + ')');
    }

    return { img: img, w: w, h: h, data: data, painted: painted, pct: pct, topColors: topColors };
}

// ---------------------------------------------------------------------------
// Seeded pseudo-RNG (Knuth LCG) — same seed always produces identical output.
// ES5 compatible; no Math.imul, no BigInt, no crypto.
// ---------------------------------------------------------------------------

function SeededRNG(seed) {
    this.s = (seed | 0) || 1;
}
SeededRNG.prototype.next = function() {
    this.s = (this.s * 1664525 + 1013904223) & 0xFFFFFFFF;
    return (this.s >>> 0) / 4294967296;
};
SeededRNG.prototype.int = function(n) {
    return (this.next() * n) | 0;
};
SeededRNG.prototype.range = function(lo, hi) {
    return lo + this.next() * (hi - lo);
};

// ---------------------------------------------------------------------------
// Semantic painter -- executes a recipe returned by /art_recipe
// ---------------------------------------------------------------------------

function executeGradientFill(data, w, h, pass) {
    var x, y, t, r, g, b, idx;
    var tr, tg, tb, br, bg, bb;
    tr = pass.top[0];    tg = pass.top[1];    tb = pass.top[2];
    br = pass.bottom[0]; bg = pass.bottom[1]; bb = pass.bottom[2];
    for (y = 0; y < h; y++) {
        t = (h > 1) ? y / (h - 1) : 0;
        r = (tr + (br - tr) * t + 0.5) | 0;
        g = (tg + (bg - tg) * t + 0.5) | 0;
        b = (tb + (bb - tb) * t + 0.5) | 0;
        for (x = 0; x < w; x++) {
            idx         = (y * w + x) * 4;
            data[idx]   = r;
            data[idx+1] = g;
            data[idx+2] = b;
            data[idx+3] = 255;
        }
    }
}

function executeNoiseScatter(data, w, h, pass) {
    var density, colors, total, i, px, py, ci, c, idx, rng;
    density = pass.density || 0.1;
    colors  = pass.colors  || [[255, 255, 255]];
    total   = (w * h * density + 0.5) | 0;
    rng     = (pass.seed !== undefined) ? new SeededRNG(pass.seed) : null;
    for (i = 0; i < total; i++) {
        px  = ((rng ? rng.next() : Math.random()) * w) | 0;
        // Scatter only in the lower 60% of the canvas (ground area).
        py  = ((rng ? rng.next() : Math.random()) * h * 0.6 + h * 0.4) | 0;
        ci  = ((rng ? rng.next() : Math.random()) * colors.length) | 0;
        c   = colors[ci];
        idx = (py * w + px) * 4;
        data[idx]   = c[0];
        data[idx+1] = c[1];
        data[idx+2] = c[2];
        data[idx+3] = 255;
    }
}

function executeEntityMarkers(data, w, h, pass) {
    var entities, i, e, px, py, c, my, mx, mmy, idx;
    entities = pass.entities || [];
    c  = pass.color    || [255, 255, 100];
    my = pass.marker_y || 0.7;
    for (i = 0; i < entities.length; i++) {
        e  = entities[i];
        px = (((e.nx || 0) * (w - 1)) + 0.5) | 0;
        py = ((my * (h - 1)) + 0.5) | 0;
        // 2x2 dot per entity
        for (mx = px; mx <= px + 1; mx++) {
            for (mmy = py; mmy <= py + 1; mmy++) {
                if (mx < 0 || mx >= w || mmy < 0 || mmy >= h) { continue; }
                idx         = (mmy * w + mx) * 4;
                data[idx]   = c[0];
                data[idx+1] = c[1];
                data[idx+2] = c[2];
                data[idx+3] = 255;
            }
        }
    }
}

// Horizontal colour band: atmosphere horizon, shoreline, treeline.
function executeHBand(data, w, h, pass) {
    var yCenter, thickness, color, yMin, yMax, x, y, idx;
    yCenter   = (pass.y         || 0.5)  * (h - 1);
    thickness = (pass.thickness || 0.03) * h;
    color     = pass.color || [200, 100, 0];
    yMin      = (yCenter - thickness * 0.5 + 0.5) | 0;
    yMax      = (yCenter + thickness * 0.5 + 0.5) | 0;
    if (yMin < 0)    { yMin = 0; }
    if (yMax >= h)   { yMax = h - 1; }
    for (y = yMin; y <= yMax; y++) {
        for (x = 0; x < w; x++) {
            idx         = (y * w + x) * 4;
            data[idx]   = color[0];
            data[idx+1] = color[1];
            data[idx+2] = color[2];
            data[idx+3] = 255;
        }
    }
}

// Sinusoidal vertical cracks: lava seams, cliff faces, cave fissures.
function executeVCrack(data, w, h, pass) {
    var count, color, yStart, yEnd, yMin, yMax, i, xCenter, xOff, x, y, idx;
    count  = pass.count   || 3;
    color  = pass.color   || [255, 100, 0];
    yMin   = ((pass.y_start || 0.0) * (h - 1) + 0.5) | 0;
    yMax   = ((pass.y_end   || 1.0) * (h - 1) + 0.5) | 0;
    for (i = 0; i < count; i++) {
        xCenter = (((i + 0.5) / count) * (w - 1) + 0.5) | 0;
        for (y = yMin; y <= yMax; y++) {
            // Subtle sinusoidal wobble per crack, seeded by index
            xOff = (Math.sin(y * 0.4 + i * 17.3) * 1.5 + 0.5) | 0;
            x    = xCenter + xOff;
            if (x < 0 || x >= w) { continue; }
            idx         = (y * w + x) * 4;
            data[idx]   = color[0];
            data[idx+1] = color[1];
            data[idx+2] = color[2];
            data[idx+3] = 255;
        }
    }
}

// Tree trunk + filled-circle canopy silhouettes along a horizon line.
function executeTreeSilhouette(data, w, h, pass) {
    var density, horizonY, colors, seed, rng, count, i, tx;
    var trunkBottom, trunkHeight, trunkTop, canopyR, canopyY;
    var dy, dx, x, y, idx, c;
    density  = pass.density   || 0.3;
    horizonY = pass.horizon_y || 0.45;
    colors   = pass.colors    || [[30, 60, 20], [40, 80, 25]];
    seed     = pass.seed      || 42;
    rng      = new SeededRNG(seed);
    count    = (w * density * 0.5 + 0.5) | 0;
    if (count < 1) { count = 1; }
    for (i = 0; i < count; i++) {
        tx          = (rng.next() * (w - 4) + 2 + 0.5) | 0;
        trunkBottom = (horizonY * (h - 1) + rng.range(-1, 2) + 0.5) | 0;
        trunkHeight = (rng.range(h * 0.07, h * 0.15) + 0.5) | 0;
        trunkTop    = trunkBottom - trunkHeight;
        if (trunkTop < 0)     { trunkTop = 0; }
        if (trunkBottom >= h) { trunkBottom = h - 1; }
        c = colors[0];
        for (y = trunkTop + (trunkHeight * 0.6 | 0); y <= trunkBottom; y++) {
            if (y < 0 || y >= h) { continue; }
            idx = (y * w + tx) * 4;
            data[idx] = c[0]; data[idx+1] = c[1]; data[idx+2] = c[2]; data[idx+3] = 255;
        }
        canopyR = (trunkHeight * 0.55 + 0.5) | 0;
        if (canopyR < 1) { canopyR = 1; }
        canopyY = trunkTop + canopyR;
        c = colors[rng.int(colors.length)];
        for (dy = -canopyR; dy <= canopyR; dy++) {
            for (dx = -canopyR; dx <= canopyR; dx++) {
                if (dx * dx + dy * dy > canopyR * canopyR) { continue; }
                x = tx + dx; y = canopyY + dy;
                if (x < 0 || x >= w || y < 0 || y >= h) { continue; }
                idx = (y * w + x) * 4;
                data[idx] = c[0]; data[idx+1] = c[1]; data[idx+2] = c[2]; data[idx+3] = 255;
            }
        }
    }
}

// Glowing particle clusters (volcanic sparks, ember drift).
function executeEmberScatter(data, w, h, pass) {
    var density, spreadRadius, seed, colors, rng, total, i, cx, cy, r, angle, px, py, idx, c;
    density      = pass.density       || 0.04;
    spreadRadius = pass.spread_radius || 0.3;
    seed         = pass.seed          || 7;
    colors       = pass.colors        || [[255, 200, 50], [255, 140, 0], [255, 60, 0]];
    rng          = new SeededRNG(seed);
    total        = (w * h * density + 0.5) | 0;
    for (i = 0; i < total; i++) {
        cx    = rng.next() * w;
        cy    = rng.range(h * 0.3, h * 0.9);
        r     = rng.next() * spreadRadius * w * 0.1;
        angle = rng.next() * 6.2832;
        px    = (cx + Math.cos(angle) * r + 0.5) | 0;
        py    = (cy + Math.sin(angle) * r + 0.5) | 0;
        if (px < 0 || px >= w || py < 0 || py >= h) { continue; }
        c   = colors[rng.int(colors.length)];
        idx = (py * w + px) * 4;
        data[idx] = c[0]; data[idx+1] = c[1]; data[idx+2] = c[2]; data[idx+3] = 255;
    }
}

// Wavy gradient band at the water/land transition.
function executeShorelineBand(data, w, h, pass) {
    var bandY, waviness, seed, colors, c0, c1, thickness;
    var waveOffsets, j, x, y, waveOff, yMin, yMax, frac, idx;
    bandY     = (pass.y        || 0.55) * (h - 1);
    waviness  = pass.waviness  || 0.04;
    seed      = pass.seed      || 3;
    colors    = pass.palette_gradient || [[80, 160, 200], [200, 220, 240]];
    thickness = (h * 0.04 + 0.5) | 0;
    if (thickness < 2) { thickness = 2; }
    c0 = colors[0];
    c1 = (colors.length > 1) ? colors[1] : colors[0];
    waveOffsets = [];
    for (j = 0; j < w; j++) {
        waveOffsets.push(Math.sin(j * 0.5 + seed * 0.1) * waviness * h);
    }
    for (x = 0; x < w; x++) {
        waveOff = waveOffsets[x];
        yMin    = (bandY + waveOff - thickness * 0.5 + 0.5) | 0;
        yMax    = (bandY + waveOff + thickness * 0.5 + 0.5) | 0;
        if (yMin < 0)  { yMin = 0; }
        if (yMax >= h) { yMax = h - 1; }
        for (y = yMin; y <= yMax; y++) {
            frac        = (yMax > yMin) ? (y - yMin) / (yMax - yMin) : 0;
            idx         = (y * w + x) * 4;
            data[idx]   = (c0[0] + (c1[0] - c0[0]) * frac + 0.5) | 0;
            data[idx+1] = (c0[1] + (c1[1] - c0[1]) * frac + 0.5) | 0;
            data[idx+2] = (c0[2] + (c1[2] - c0[2]) * frac + 0.5) | 0;
            data[idx+3] = 255;
        }
    }
}

// Small light-pixel clusters near the shoreline (seafoam, spray).
function executeFoamScatter(data, w, h, pass) {
    var density, clusterSize, maskBias, seed, rng, total, i, cx, cy, j, px, py, idx;
    density     = pass.density      || 0.04;
    clusterSize = pass.cluster_size || 2;
    maskBias    = pass.mask_bias    || 0.55;
    seed        = pass.seed         || 11;
    rng         = new SeededRNG(seed);
    total       = (w * density * 3 + 0.5) | 0;
    for (i = 0; i < total; i++) {
        cx = (rng.next() * w + 0.5) | 0;
        cy = (rng.range(maskBias - 0.05, maskBias + 0.05) * (h - 1) + 0.5) | 0;
        for (j = 0; j < clusterSize * clusterSize; j++) {
            px  = (cx + rng.range(-clusterSize, clusterSize) + 0.5) | 0;
            py  = (cy + rng.range(-clusterSize * 0.5, clusterSize * 0.5) + 0.5) | 0;
            if (px < 0 || px >= w || py < 0 || py >= h) { continue; }
            idx         = (py * w + px) * 4;
            data[idx]   = (230 + rng.next() * 25 + 0.5) | 0;
            data[idx+1] = (235 + rng.next() * 20 + 0.5) | 0;
            data[idx+2] = (240 + rng.next() * 15 + 0.5) | 0;
            data[idx+3] = 255;
        }
    }
}

// Downward triangular formations hanging from the top (cave stalactites).
function executeStalactiteSilhouette(data, w, h, pass) {
    var density, seed, colors, rng, count, i, tx, tipY, baseHalf, y, x, xWidth, idx, c;
    density = pass.density || 0.4;
    seed    = pass.seed    || 13;
    colors  = pass.colors  || [[15, 15, 25], [20, 20, 35]];
    rng     = new SeededRNG(seed);
    count   = (w * density * 0.4 + 0.5) | 0;
    if (count < 1) { count = 1; }
    for (i = 0; i < count; i++) {
        tx       = (rng.next() * (w - 4) + 2 + 0.5) | 0;
        tipY     = (rng.range(0.2, 0.5) * (h - 1) + 0.5) | 0;
        baseHalf = (rng.range(2, 5) + 0.5) | 0;
        c = colors[rng.int(colors.length)];
        for (y = 0; y <= tipY; y++) {
            xWidth = (baseHalf * (1 - y / (tipY || 1)) + 0.5) | 0;
            for (x = tx - xWidth; x <= tx + xWidth; x++) {
                if (x < 0 || x >= w) { continue; }
                idx = (y * w + x) * 4;
                data[idx] = c[0]; data[idx+1] = c[1]; data[idx+2] = c[2]; data[idx+3] = 255;
            }
        }
    }
}

// Thin vertical reed groups clustered along the horizon (swamp/wetland).
function executeReedCluster(data, w, h, pass) {
    var density, seed, colors, rng, count, i, cx, ccount, j, rx, reedBottom, rh, reedTop, y, idx, c;
    density = pass.density || 0.3;
    seed    = pass.seed    || 17;
    colors  = pass.colors  || [[70, 90, 40], [90, 110, 50], [50, 70, 30]];
    rng     = new SeededRNG(seed);
    count   = (w * density * 0.3 + 0.5) | 0;
    if (count < 1) { count = 1; }
    for (i = 0; i < count; i++) {
        cx     = (rng.next() * (w - 4) + 2 + 0.5) | 0;
        ccount = (rng.range(2, 5) + 0.5) | 0;
        for (j = 0; j < ccount; j++) {
            rx         = (cx + rng.range(-3, 3) + 0.5) | 0;
            if (rx < 0 || rx >= w) { continue; }
            reedBottom = ((0.5 + rng.range(0.05, 0.15)) * (h - 1) + 0.5) | 0;
            rh         = (rng.range(h * 0.08, h * 0.18) + 0.5) | 0;
            reedTop    = reedBottom - rh;
            if (reedTop < 0)     { reedTop = 0; }
            if (reedBottom >= h) { reedBottom = h - 1; }
            c = colors[rng.int(colors.length)];
            for (y = reedTop; y <= reedBottom; y++) {
                idx = (y * w + rx) * 4;
                data[idx] = c[0]; data[idx+1] = c[1]; data[idx+2] = c[2]; data[idx+3] = 255;
            }
        }
    }
}

// Dense low-visibility scatter for swamp floor murk.
function executeMurkNoise(data, w, h, pass) {
    var density, seed, colors, rng, total, i, px, py, c, idx;
    density = pass.density || 0.15;
    seed    = pass.seed    || 5;
    colors  = pass.colors  || [[50, 70, 35], [40, 60, 25], [60, 80, 40]];
    rng     = new SeededRNG(seed);
    total   = (w * h * density + 0.5) | 0;
    for (i = 0; i < total; i++) {
        px  = (rng.next() * w) | 0;
        py  = (rng.range(0.45, 1.0) * (h - 1) + 0.5) | 0;
        c   = colors[rng.int(colors.length)];
        idx = (py * w + px) * 4;
        data[idx] = c[0]; data[idx+1] = c[1]; data[idx+2] = c[2]; data[idx+3] = 255;
    }
}

// Execute all recipe passes, write once to canvas, return pass count.
function executeRecipe(recipe, info) {
    var passes, i, pass, data, img, w, h;
    img    = info.img;
    w      = info.w;
    h      = info.h;
    data   = info.data;
    passes = recipe.passes || [];
    for (i = 0; i < passes.length; i++) {
        pass = passes[i];
        if (pass.type === 'gradient_fill') {
            executeGradientFill(data, w, h, pass);
        } else if (pass.type === 'noise_scatter') {
            executeNoiseScatter(data, w, h, pass);
        } else if (pass.type === 'h_band') {
            executeHBand(data, w, h, pass);
        } else if (pass.type === 'v_crack') {
            executeVCrack(data, w, h, pass);
        } else if (pass.type === 'tree_silhouette') {
            executeTreeSilhouette(data, w, h, pass);
        } else if (pass.type === 'ember_scatter') {
            executeEmberScatter(data, w, h, pass);
        } else if (pass.type === 'shoreline_band') {
            executeShorelineBand(data, w, h, pass);
        } else if (pass.type === 'foam_scatter') {
            executeFoamScatter(data, w, h, pass);
        } else if (pass.type === 'stalactite_silhouette') {
            executeStalactiteSilhouette(data, w, h, pass);
        } else if (pass.type === 'reed_cluster') {
            executeReedCluster(data, w, h, pass);
        } else if (pass.type === 'murk_noise') {
            executeMurkNoise(data, w, h, pass);
        } else if (pass.type === 'entity_marker') {
            executeEntityMarkers(data, w, h, pass);
        }
    }
    img.putImageData(data);
    return passes.length;
}

// Apply an array of {x, y, r, g, b, a} actions onto the canvas image data.
function applyActions(img, data, actions) {
    var w, h, applied, i, act, x, y, idx;
    w       = img.width;
    h       = img.height;
    applied = 0;
    for (i = 0; i < actions.length; i++) {
        act = actions[i];
        x   = act.x | 0;
        y   = act.y | 0;
        if (x < 0 || x >= w || y < 0 || y >= h) { continue; }
        idx         = (y * w + x) * 4;
        data[idx]   = act.r & 0xFF;
        data[idx+1] = act.g & 0xFF;
        data[idx+2] = act.b & 0xFF;
        data[idx+3] = (act.a !== undefined ? act.a : 255) & 0xFF;
        applied++;
    }
    img.putImageData(data);
    return applied;
}

// ---------------------------------------------------------------------------
// Ollama guidance  (mode: "ollama")
// ---------------------------------------------------------------------------

function buildOllamaPrompt(info) {
    var colors = info.topColors.length ? info.topColors.join(', ') : 'none';
    return 'You are an AI pixel artist contributing to the EngAIn game world.\n'
        + 'Art intent: ' + engain.settings.artIntent + '\n'
        + 'Canvas: ' + info.w + 'x' + info.h + ' pixels. ' + info.pct + '% painted.\n'
        + 'Dominant colors so far: ' + colors + '\n'
        + '\n'
        + 'Suggest the next 5 pixel placements to advance this sprite.\n'
        + 'Respond ONLY with this exact JSON - no prose, no markdown:\n'
        + '{"actions":[{"x":0,"y":0,"r":255,"g":128,"b":0,"a":255,"reason":"warm highlight"}]}';
}

function requestOllamaGuidance(info, cb) {
    postJSON(engain.settings.ollamaEndpoint + '/api/generate', {
        model:  engain.settings.model,
        prompt: buildOllamaPrompt(info),
        stream: false,
        format: "json"
    }, function(data, err) {
        var parsed;
        if (err) { cb(null, err); return; }
        try {
            parsed = (typeof data.response === 'string') ? JSON.parse(data.response) : data;
            cb(parsed.actions || [], null);
        } catch (ex) {
            cb(null, 'Ollama response parse failed: ' + ex);
        }
    });
}

// ---------------------------------------------------------------------------
// Empire guidance  (mode: "empire") -- ZW Protocol, mirrors empire_bridge.py
// ---------------------------------------------------------------------------

function requestEmpireGuidance(info, cb) {
    var sid = engain.settings.sessionId || ('trixelpixel_' + Date.now());
    postJSON(engain.settings.empireEndpoint + '/orchestrate', {
        session_id: sid,
        domain:     "trixel_creative",
        zw_content: {
            "!zw/trixel.guidance_request": {
                canvas_summary: {
                    width:           info.w,
                    height:          info.h,
                    painted_pct:     info.pct,
                    dominant_colors: info.topColors
                },
                current_tool:    "brush",
                art_intent:      engain.settings.artIntent,
                request_type:    "creative_suggestion",
                zw_version:      BRIDGE_VERSION
            }
        }
    }, function(data, err) {
        var act, c;
        if (err) { cb(null, err); return; }
        try {
            if (data.ai_suggestion && data.ai_suggestion["!zw/art.action"]) {
                act = data.ai_suggestion["!zw/art.action"];
                c   = act.color || [255, 255, 255];
                cb([{ x: act.x || 8, y: act.y || 8,
                      r: c[0], g: c[1], b: c[2], a: 255,
                      reason: act.reasoning || '' }], null);
            } else if (data.actions && data.actions.length) {
                cb(data.actions, null);
            } else {
                cb(null, 'Empire: no actions in response');
            }
        } catch (ex) {
            cb(null, 'Empire parse error: ' + ex);
        }
    });
}

// ---------------------------------------------------------------------------
// Scene intent fetch -- pulls ZW art intent from EngAIn scene server
// ---------------------------------------------------------------------------

function fetchSceneIntent(cb) {
    httpGet(engain.settings.sceneEndpoint, function(rsp) {
        if (rsp.status !== 200) { cb(null, 'scene server: HTTP ' + rsp.status); return; }
        try { cb(JSON.parse(rsp.text), null); }
        catch (ex) { cb(null, 'scene parse: ' + ex); }
    });
}

// ---------------------------------------------------------------------------
// Learning feedback (fire-and-forget)
// ---------------------------------------------------------------------------

function sendFeedback(actions, success) {
    var sid = engain.settings.sessionId || ('trixelpixel_' + Date.now());
    var key = engain.nextId++ + 'e';
    storage.fetch(
        engain.settings.empireEndpoint + '/orchestrate', key, "",
        "POST", JSON.stringify({
            session_id: sid,
            domain:     "trixel_creative",
            zw_content: {
                "!zw/trixel.learning": {
                    session_id:          sid,
                    actions_applied:     actions,
                    canvas_evolution:    success ? "positive" : "rejected",
                    style_notes:         engain.settings.artIntent,
                    preference_learning: true,
                    zw_version:          BRIDGE_VERSION
                }
            }
        }),
        "Content-Type", "application/json"
    );
    // No callback registered -- feedback is fire-and-forget.
}

// ---------------------------------------------------------------------------
// UI views  (same declarative pattern as ai.js)
// ---------------------------------------------------------------------------

var views = {
    main: [
        { type: 'label', text: 'EngAIn ZW Bridge  v' + BRIDGE_VERSION },
        { type: 'break' },
        { type: 'label', text: function() { return 'Mode: ' + engain.settings.mode; } },
        { type: 'break' },
        { type: 'label', text: function() {
            var s = engain.settings.artIntent;
            return 'Intent: ' + (s.length > 40 ? s.substring(0, 40) + '...' : s);
        }},
        { type: 'break' },
        {
            type: 'button', text: 'Run Guidance',
            click: function() {
                var info = getCanvasInfo();
                if (!info) { console.log('[EngAIn] No active sprite or cel.'); return; }
                engain.view('wait');
                engain.runGuidance(info);
            }
        },
        {
            type: 'button', text: 'Fetch Scene Intent',
            click: function() {
                engain.view('wait');
                fetchSceneIntent(function(data, err) {
                    engain.close('wait');
                    if (err) { console.log('[EngAIn] Scene error: ' + err); return; }
                    if (data && (data.art_intent || data.artIntent)) {
                        engain.settings.artIntent = data.art_intent || data.artIntent;
                        engain.saveSettings();
                        console.log('[EngAIn] Intent updated: ' + engain.settings.artIntent);
                    }
                });
            }
        },
        {
            type: 'button', text: 'Paint Scene',
            click: function() {
                var info = getCanvasInfo();
                if (!info) { console.log('[EngAIn] No active sprite or cel.'); return; }
                engain.view('wait');
                httpGet(engain.settings.recipeEndpoint, function(rsp) {
                    var resp, recipe, n;
                    engain.close('wait');
                    if (rsp.status !== 200) {
                        console.log('[EngAIn] Recipe server: HTTP ' + rsp.status);
                        return;
                    }
                    try {
                        resp = JSON.parse(rsp.text);
                        if (!resp || resp.status !== 'success' || !resp.recipe) {
                            console.log('[EngAIn] Recipe error: ' + (resp ? resp.message : 'empty response'));
                            return;
                        }
                        recipe = resp.recipe;
                        info   = getCanvasInfo();
                        if (!info) { return; }
                        n = executeRecipe(recipe, info);
                        console.log('[EngAIn] Painted ' + n + ' passes: '
                            + recipe.label + ' (' + recipe.terrain + ')  '
                            + (recipe.entity_count || 0) + ' entities');
                    } catch (ex) {
                        console.log('[EngAIn] Paint error: ' + ex);
                    }
                });
            }
        },
        { type: 'break' },
        {
            type: 'button', text: 'Config...',
            click: function() { engain.view('config'); }
        }
    ],

    wait: [
        { canClose: false },
        { type: 'label', text: 'Requesting AI guidance...' }
    ],

    config: [
        { type: 'label',  text: 'Mode (ollama / empire):' },
        { type: 'break' },
        { type: 'entry',  maxsize: 16,  bind: 'settings.mode' },
        { type: 'break' },
        { type: 'label',  text: 'Art Intent:' },
        { type: 'break' },
        { type: 'entry',  maxsize: 128, bind: 'settings.artIntent' },
        { type: 'break' },
        { type: 'label',  text: 'Ollama Model:' },
        { type: 'break' },
        { type: 'entry',  maxsize: 64,  bind: 'settings.model' },
        { type: 'break' },
        { type: 'label',  text: 'Ollama Endpoint:' },
        { type: 'break' },
        { type: 'entry',  maxsize: 64,  bind: 'settings.ollamaEndpoint' },
        { type: 'break' },
        { type: 'label',  text: 'Empire Endpoint:' },
        { type: 'break' },
        { type: 'entry',  maxsize: 64,  bind: 'settings.empireEndpoint' },
        { type: 'break' },
        { type: 'label',  text: 'Scene Server Endpoint:' },
        { type: 'break' },
        { type: 'entry',  maxsize: 64,  bind: 'settings.sceneEndpoint' },
        { type: 'break' },
        { type: 'label',  text: 'Art Recipe Endpoint:' },
        { type: 'break' },
        { type: 'entry',  maxsize: 64,  bind: 'settings.recipeEndpoint' },
        { type: 'break' },
        { type: 'label',  text: 'Auto-apply without preview (1=yes, 0=no):' },
        { type: 'break' },
        { type: 'entry',  maxsize: 4,   bind: 'settings.autoApply' },
        { type: 'break' },
        {
            type: 'button', text: 'Save & Back',
            click: function() {
                engain.saveSettings();
                engain.close('config');
            }
        }
    ],

    result: [
        {
            type: 'label',
            text: function() { return engain._lastResultMsg || 'AI guidance ready.'; }
        },
        { type: 'break' },
        {
            type: 'button', text: 'Apply',
            click: function() {
                var info, n;
                if (engain._pendingActions) {
                    info = getCanvasInfo();
                    if (info) {
                        n = applyActions(info.img, info.data, engain._pendingActions);
                        console.log('[EngAIn] Applied ' + n + ' pixel(s).');
                        sendFeedback(engain._pendingActions, true);
                    }
                    engain._pendingActions = null;
                }
                engain.close('result');
            }
        },
        {
            type: 'button', text: 'Discard',
            click: function() {
                sendFeedback(engain._pendingActions || [], false);
                engain._pendingActions = null;
                engain.close('result');
            }
        }
    ]
};

// ---------------------------------------------------------------------------
// EngAIn controller
// ---------------------------------------------------------------------------

function EngAIn() {
    var k, s, saved;
    s = {};
    for (k in defaultSettings) {
        if (defaultSettings.hasOwnProperty(k)) {
            s[k] = defaultSettings[k];
        }
    }
    s.sessionId = 'trixelpixel_' + Date.now();

    this.settings        = s;
    this.nextId          = 1;
    this.dlg             = null;
    this.stack           = [];
    this._pendingActions = null;
    this._lastResultMsg  = '';

    if (storage.load('settings', 'engain_bridge')) {
        try {
            saved = JSON.parse(storage.get('settings', 'engain_bridge'));
            for (k in saved) {
                if (saved.hasOwnProperty(k)) {
                    this.settings[k] = saved[k];
                }
            }
        } catch (ex) {
            console.log('[EngAIn] Could not load saved settings: ' + ex);
        }
    }
}

EngAIn.prototype.init = function() {
    this.view('main');
};

EngAIn.prototype.saveSettings = function() {
    storage.set(JSON.stringify(this.settings), 'settings', 'engain_bridge');
    storage.save('settings', 'engain_bridge');
};

EngAIn.prototype.runGuidance = function(info) {
    var mode = (this.settings.mode || 'ollama').toLowerCase();
    var self = this;

    function onGuidance(actions, err) {
        var n, msg, i, a;
        self.close('wait');
        if (err) {
            console.log('[EngAIn] Guidance error: ' + err);
            return;
        }
        if (!actions || !actions.length) {
            console.log('[EngAIn] No actions returned.');
            return;
        }
        if (self.settings.autoApply === '1') {
            n = applyActions(info.img, info.data, actions);
            console.log('[EngAIn] Auto-applied ' + n + ' pixel(s).');
            sendFeedback(actions, true);
        } else {
            msg = 'AI suggests ' + actions.length + ' pixel(s):';
            for (i = 0; i < actions.length; i++) {
                a = actions[i];
                msg = msg + '\n  (' + a.x + ',' + a.y + ') '
                    + 'rgb(' + a.r + ',' + a.g + ',' + a.b + ')'
                    + (a.reason ? ' - ' + a.reason : '');
            }
            self._pendingActions = actions;
            self._lastResultMsg  = msg;
            self.view('result');
        }
    }

    if (mode === 'empire') {
        requestEmpireGuidance(info, onGuidance);
    } else {
        requestOllamaGuidance(info, onGuidance);
    }
};

EngAIn.prototype.getSetting = function(path, defval) {
    var obj = this;
    var parts = (path + '').split('.');
    var k;
    while (parts.length) {
        k = parts.shift();
        if (!obj || !(k in obj)) { return defval; }
        obj = obj[k];
    }
    return obj;
};

EngAIn.prototype.setSetting = function(path, value) {
    var obj = this;
    var parts = (path + '').split('.');
    var k;
    while (parts.length) {
        k = parts.shift();
        if (parts.length) {
            obj = obj[k];
        } else {
            obj[k] = value;
            this.saveSettings();
        }
    }
};

EngAIn.prototype.close = function(name) {
    var n;
    if (!this.stack.length) { return; }
    if (this.stack[this.stack.length - 1].name !== name) { return; }
    if (this.dlg) { this.dlg.close(); this.dlg = null; }
    this.stack.pop();
    if (!this.stack.length) { return; }
    n = this.stack[this.stack.length - 1].name;
    this.stack.pop();
    this.view(n);
};

EngAIn.prototype.view = function(name, isTmp) {
    var dlgId, dlg, self;

    if (this.dlg) { this.dlg.close(); this.dlg = null; }
    if (!views[name]) { console.log('[EngAIn] Unknown view: ' + name); return; }

    dlgId = this.nextId++;
    dlg   = this.dlg = app.createDialog(dlgId + 'D');
    self  = this;

    this[dlgId + 'D_close'] = this._close.bind(this, dlgId);

    if (this.stack.length && this.stack[this.stack.length - 1].isTmp) {
        this.stack.pop();
    }
    this.stack.push({ name: name, dlgId: dlgId, isTmp: isTmp });

    dlg.title = 'EngAIn: ' + name.replace(/_/g, ' ')
        .replace(/(^| )(.)/g, function(_, sp, ch) { return sp + ch.toUpperCase(); });

    process(views[name]);

    // Declared here so hoisting makes them available to the process() call above.
    function process(viewMeta) {
        var i, node, nodeType, click, btn, entry, nodeCopy, nk, dk;
        for (i = 0; i < viewMeta.length; i++) {
            node = viewMeta[i];

            if (typeof node.bind === 'string') {
                nodeCopy = {};
                for (nk in node) {
                    if (node.hasOwnProperty(nk)) { nodeCopy[nk] = node[nk]; }
                }
                nodeCopy.value  = self.getSetting(node.bind, node.value);
                nodeCopy.change = self.setSetting.bind(self, node.bind);
                node = nodeCopy;
            }

            nodeType = getVal(node, 'type', 'special').toLowerCase();

            if (nodeType === 'label') {
                dlg.addLabel(getVal(node, 'text', getVal(node, 'value', '')), self.nextId++ + 'L');

            } else if (nodeType === 'button') {
                click = node.click;
                if (typeof click === 'string') {
                    click = (function(n) { return function() { self.view(n); }; })(click);
                }
                btn = dlg.addButton(getVal(node, 'text', ''), self.nextId + 'B');
                self[self.nextId + 'B_click'] = click.bind(btn);
                self.nextId++;

            } else if (nodeType === 'break') {
                dlg.addBreak();

            } else if (nodeType === 'entry') {
                if (node.change) {
                    self[self.nextId + 'E_change'] = (function(id, cb) {
                        return function() { cb(storage.get(id + 'E')); };
                    })(self.nextId, node.change);
                }
                entry = dlg.addEntry(getVal(node, 'text', ''), self.nextId++ + 'E');
                entry.maxsize = getVal(node, 'maxsize', 40);
                entry.value   = getVal(node, 'value', '');

            } else {
                // special: canClose, dynamic, conditional sub-views
                if (typeof node['if'] === 'function') {
                    if (node['if']()) { process(node.then); }
                } else if (typeof node.dynamic === 'function') {
                    process(node.dynamic());
                } else {
                    for (dk in node) {
                        if (node.hasOwnProperty(dk)) { dlg[dk] = node[dk]; }
                    }
                }
            }
        }
    }

    function getVal(obj, key, def) {
        if (!(key in obj)) { return def; }
        return (typeof obj[key] === 'function') ? obj[key]() : obj[key];
    }
};

EngAIn.prototype._close = function(dlgId) {
    var name;
    if (!this.stack.length) { return; }
    if (this.stack[this.stack.length - 1].dlgId !== dlgId) { return; }
    this.stack.pop();
    if (!this.stack.length) { return; }
    name = this.stack[this.stack.length - 1].name;
    this.stack.pop();
    this.view(name);
};

// ---------------------------------------------------------------------------
// Global event dispatch -- same pattern as ai.js
// Routes all engine events: init, button clicks, entry changes, fetch callbacks
// ---------------------------------------------------------------------------

function onEvent(event) {
    if (typeof engain === 'undefined') { engain = new EngAIn(); }
    if (typeof engain[event] === 'function') { engain[event](); }
}
