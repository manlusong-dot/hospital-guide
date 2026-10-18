const api = require('../../utils/api');
const req = require('../../utils/request');

const FIXED_PLACES = ['主入口', '急诊入口', '儿科入口', '检验入口', '西药房取药窗口', '中药房',
  '挂号收费处', '收费处', '取报告处(检验科)', '检验科'];

function displayPlaceLabel(ref) {
  const value = String(ref || '');
  if (/^\d+f_poi_cfy$/.test(value) || /^\d+f_poi_cfy\d+$/.test(value)) return '挂号收费处';
  if (/^\d+f_poi_hzc$/.test(value)) return '候诊处';
  return value;
}

Page({
  data: {
    floors: [1, 2, 3, 4],
    placeOptions: [],
    startNames: [],
    endNames: [],
    startIndex: 0,
    endIndex: 0,
    route: null,
    currentFloor: 1,
    routeFloors: { 1: false, 2: false, 3: false, 4: false },
    voiceEnabled: true,
    loading: false,
    hasJourney: false,
    endRef: '',
    startRef: ''
  },

  onLoad: function (options) {
    this._initTTS();
    const self = this;
    api.departments().then(function (depts) {
      const names = FIXED_PLACES.concat(depts.map(function (d) { return d.name; }));
      self.setData({
        placeOptions: names,
        startNames: names,
        endNames: names
      });
      if (self._pendingTarget) {
        self.applyTarget(self._pendingTarget);
        self._pendingTarget = '';
      }
    }).catch(function (err) {
      req.showError(err);
    });
    this.drawMap();
  },

  onShow: function () {
    const target = getApp().globalData.navTarget;
    const startTarget = getApp().globalData.navStartTarget || '';
    const sessionId = getApp().globalData.sessionId;
    const currentDept = getApp().globalData.currentDept;
    this.setData({ hasJourney: !!(sessionId && currentDept) });
    // 设置起点 - 如果列表还没加载完，等加载完再设置
    if (startTarget) {
      getApp().globalData.navStartTarget = '';
      if (this.data.startNames.length > 0) {
        this._applyStartTarget(startTarget);
      } else {
        this._pendingStartTarget = startTarget;
      }
    }
    if (target) {
      getApp().globalData.navTarget = '';
      if (this.data.placeOptions.length > 0) {
        this.applyTarget(target);
      } else {
        this._pendingTarget = target;
      }
    }
  },

  _applyStartTarget: function (startTarget) {
    const names = this.data.startNames;
    let idx = names.indexOf(startTarget);
    if (idx < 0) {
      for (let i = 0; i < names.length; i++) {
        if (names[i].indexOf(startTarget) >= 0 || startTarget.indexOf(names[i]) >= 0) {
          idx = i;
          break;
        }
      }
    }
    if (idx >= 0) {
      this.setData({ startIndex: idx });
    }
  },

  applyTarget: function (target) {
    const names = this.data.endNames;
    const ref = target && typeof target === 'object' ? target.ref : target;
    const label = target && typeof target === 'object'
      ? (target.label || displayPlaceLabel(ref))
      : displayPlaceLabel(target);
    let idx = names.indexOf(label);
    if (idx < 0) {
      for (let i = 0; i < names.length; i++) {
        if (names[i].indexOf(label) >= 0 || label.indexOf(names[i]) >= 0) {
          idx = i;
          break;
        }
      }
    }
    if (idx < 0) {
      // 聊天助手可以传入地图节点 ID，临时加入显示列表后直接规划路线。
      idx = names.length;
      this.setData({
        endNames: names.concat([label]),
        placeOptions: this.data.placeOptions.concat([label]),
        endIndex: idx,
        endRef: ref || ''
      }, this.startNavigate.bind(this));
      return;
    }
    this.setData({ endIndex: idx, endRef: ref || '' }, this.startNavigate.bind(this));
  },

  onStartChange: function (e) {
    this.setData({ startIndex: Number(e.detail.value), startRef: '' });
  },

  onEndChange: function (e) {
    this.setData({ endIndex: Number(e.detail.value), endRef: '' });
  },

  startNavigate: function () {
    const self = this;
    const start = this.data.startRef || this.data.startNames[this.data.startIndex];
    const end = this.data.endRef || this.data.endNames[this.data.endIndex];
    if (start === end) {
      wx.showToast({ title: '起点和终点不能相同', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    api.navigate(start, end).then(function (route) {
      const floorsMap = { 1: false, 2: false, 3: false, 4: false };
      route.segments.forEach(function (s) { floorsMap[s.floor] = true; });
      self.setData({
        route: route,
        routeFloors: floorsMap,
        currentFloor: route.segments[0].floor,
        loading: false
      });
      self.drawMap();
      self.speak('已为您规划从' + route.start.name + '到' + route.end.name +
        '的路线，约' + route.distance_m + '米，全程' + route.steps.length + '步');
    }).catch(function (err) {
      self.setData({ loading: false });
      req.showError(err);
    });
  },

  switchFloor: function (e) {
    const floor = Number(e.currentTarget.dataset.floor);
    if (!floor) return;
    const self = this;
    this.setData({ currentFloor: floor }, function () {
      self.drawMap();
    });
  },

  onMapTap: function (e) {
    const marker = this._floorChangeMarker;
    if (!marker || !e.touches || !e.touches[0]) return;
    const touch = e.touches[0];
    const dx = touch.x - marker.x;
    const dy = touch.y - marker.y;
    if (dx * dx + dy * dy > marker.radius * marker.radius) return;
    this._goToFloor(marker);
  },

  _goToFloor: function (marker) {
    const self = this;
    const floor = marker.nextFloor;
    const speakText = marker.guidance + (marker.notice ? ('。' + marker.notice) : '');
    // 换层前先语音提示怎么坐、坐到几楼
    this.speak(speakText);
    this.setData({ currentFloor: floor }, function () { self.drawMap(); });
    wx.showToast({ title: '已到' + floor + '楼，注意核对楼层标识', icon: 'none', duration: 2500 });
    // 到达后再补一句确认, 提醒用户核对是不是目标楼层
    setTimeout(function () {
      self.speak('已到' + floor + '楼，请确认这是不是目标楼层');
    }, 1800);
  },

  drawMap: function () {
    const self = this;
    const floor = this.data.currentFloor;
    const route = this.data.route;
    this._floorChangeMarker = null;
    wx.createSelectorQuery().select('#mapCanvas').fields({ node: true, size: true }).exec(function (res) {
      if (!res || !res[0] || !res[0].node) return;
      const canvas = res[0].node;
      const ctx = canvas.getContext('2d');
      const width = res[0].width;
      const height = res[0].height;
      const dpr = wx.getWindowInfo ? wx.getWindowInfo().pixelRatio : wx.getSystemInfoSync().pixelRatio;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
      const img = canvas.createImage();
      img.onload = function () {
        ctx.drawImage(img, 0, 0, width, height);
        const scale = width / 1200;
        const seg = route ? route.segments.filter(function (s) { return s.floor === floor; })[0] : null;
        if (seg && seg.points.length > 1) {
          ctx.strokeStyle = '#007AFF';
          ctx.lineWidth = 8;
          ctx.lineJoin = 'round';
          ctx.lineCap = 'round';
          ctx.beginPath();
          seg.points.forEach(function (p, i) {
            const x = p[0] * scale;
            const y = p[1] * scale;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          });
          ctx.stroke();
          self.drawMarker(ctx, seg.points[0][0] * scale, seg.points[0][1] * scale, '#34C759', '起');
          const last = seg.points[seg.points.length - 1];
          const segmentIndex = route.segments.indexOf(seg);
          const isFinal = segmentIndex === route.segments.length - 1;
          if (!isFinal) {
            // 跳过纯途经的换层楼层(如手扶梯 1F->2F->3F 的 2F), 直接跳到真正需要行走的到达楼层
            var j = segmentIndex + 1;
            while (j < route.segments.length - 1 && route.segments[j].pass) { j++; }
            var nextFloor = route.segments[j].floor;
            var vertStep = null;
            (route.steps || []).forEach(function (s) {
              if (s.kind && s.kind !== 'walk' && s.kind !== 'arrive' && s.floor === nextFloor) {
                vertStep = s;
              }
            });
            self._floorChangeMarker = {
              x: last[0] * scale,
              y: last[1] * scale,
              radius: 42,
              nextFloor: nextFloor,
              guidance: vertStep ? vertStep.text : ('换到' + nextFloor + '楼'),
              notice: vertStep ? (vertStep.notice || '') : ''
            };
          }
          self.drawMarker(ctx, last[0] * scale, last[1] * scale, isFinal ? '#FF3B30' : '#FF9500', isFinal ? '终' : '换');
        }
      };
      img.src = '/static/floors/floor' + floor + '.jpg';
    });
  },

  drawMarker: function (ctx, x, y, color, label) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 16, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 18px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, x, y);
  },

  /* ---------- 语音提示小助手 ---------- */
  _initTTS: function () {
    if (this._ttsChecked) return;
    this._ttsChecked = true;
    this._ttsManager = null;
    try {
      // 微信同声传译插件: 语音合成; 未授权/不可用时静默降级为纯文字提示
      var plugin = requirePlugin('WechatSI');
      this._ttsManager = plugin.getTextToSpeechManager();
    } catch (err) {
      this._ttsManager = null;
    }
  },

  speak: function (text) {
    if (!this.data.voiceEnabled || !text) return;
    this._initTTS();
    var manager = this._ttsManager;
    if (!manager || !manager.speak) return;
    manager.speak({
      lang: 'zh_CN',
      text: String(text).replace(/\s+/g, ' '),
      success: function () {},
      fail: function () {}
    });
  },

  toggleVoice: function (e) {
    var on = !!(e && e.detail && e.detail.value);
    this.setData({ voiceEnabled: on });
    if (on) {
      this.speak('语音提示已开启');
    } else {
      this.speak('语音提示已关闭');
    }
  },

  speakRoute: function () {
    const route = this.data.route;
    if (!route) return;
    var texts = (route.steps || []).map(function (s) {
      return s.text + (s.notice ? ('。' + s.notice) : '');
    });
    this.speak('从' + route.start.name + '到' + route.end.name + '，约' +
      route.distance_m + '米。' + texts.join('，'));
  },

  goJourney: function () {
    const sessionId = getApp().globalData.sessionId;
    const currentDept = getApp().globalData.currentDept;
    if (sessionId && currentDept) {
      wx.navigateTo({ url: '/pages/journey/journey?session=' + sessionId + '&dept=' + currentDept.id });
    }
  }
});
