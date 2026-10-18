const api = require('../../utils/api');
const req = require('../../utils/request');

function displayPlaceLabel(ref) {
  const value = String(ref || '');
  if (/^\d+f_poi_cfy$/.test(value) || /^\d+f_poi_cfy\d+$/.test(value)) return '挂号收费处';
  if (/^\d+f_poi_hzc$/.test(value)) return '候诊处';
  return value;
}

Page({
  data: {
    sessionId: '',
    deptId: '',
    deptList: [],
    card: null,
    step: null,
    state: null,
    showPicker: false,
    showCompleteModal: false,
    readOnly: false,
    placeTarget: '',
    placeLabel: '',
    examOrderText: ''
  },

  onLoad: function (options) {
    const session = options.session || getApp().globalData.sessionId || '';
    const dept = options.dept || (getApp().globalData.currentDept ? getApp().globalData.currentDept.id : '');
    if (session && dept) {
      this.setData({ sessionId: session, deptId: dept });
      getApp().globalData.sessionId = session;
      getApp().globalData.currentDept = { id: dept };
      this.loadCardForSession(dept, session);
    } else if (session) {
      // 只有 sessionId，尝试从后端恢复科室信息
      const self = this;
      this.setData({ sessionId: session });
      api.journeyState(session).then(function (res) {
        if (res.state && res.state.dept_id) {
          self.setData({ deptId: res.state.dept_id });
          getApp().globalData.currentDept = { id: res.state.dept_id };
          self.loadCardForSession(res.state.dept_id, session);
        } else {
          self.loadDepts();
        }
      }).catch(function () {
        self.loadDepts();
      });
    } else {
      this.loadDepts();
    }
  },

  loadDepts: function () {
    const self = this;
    api.departments().then(function (list) {
      const clinic = list.filter(function (d) {
        return d.category === '门诊' || d.category === '检查' || d.category === '急诊';
      });
      self.setData({ deptList: clinic, showPicker: true });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  pickDept: function (e) {
    const dept = this.data.deptList[e.currentTarget.dataset.index];
    const self = this;
    api.journeySession(null, dept.id).then(function (res) {
      getApp().globalData.sessionId = res.session_id;
      getApp().globalData.currentDept = dept;
      self.setData({
        sessionId: res.session_id,
        deptId: dept.id,
        showPicker: false,
        card: res.card,
        step: res.step,
        state: null,
        readOnly: false,
        showCompleteModal: false
      });
      self.applyStepPlace(res.step);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  loadCard: function (deptId) {
    const self = this;
    api.journeyCard(deptId).then(function (card) {
      self.setData({ card: card });
      self.refreshStep();
    }).catch(function (err) {
      req.showError(err);
    });
  },

  loadCardForSession: function (deptId, sessionId) {
    const self = this;
    api.journeyState(sessionId).then(function (res) {
      self.setData({
        state: res.state,
        readOnly: !!res.state.finished,
        examOrderText: (res.state.exams || []).join('、')
      });
      return api.journeyCard(deptId, res.state.exams || []);
    }).then(function (card) {
      self.setData({ card: card });
      self.refreshStep();
    }).catch(function (err) {
      req.showError(err);
    });
  },

  refreshStep: function () {
    const self = this;
    api.journeyState(this.data.sessionId).then(function (res) {
      self.setData({ step: res.step, state: res.state, readOnly: !!res.state.finished });
      self.applyStepPlace(res.step);
    }).catch(function () {
      self.setData({ step: null });
    });
  },

  applyStepPlace: function (step) {
    if (!step || !this.data.card) return;
    const item = this.data.card.steps[step.index];
    this.setData({
      placeTarget: item && item.nav_target ? item.nav_target : '',
      placeLabel: item && item.nav_target ? displayPlaceLabel(item.nav_label || item.nav_target) : ''
    });
  },

  onExamOrderInput: function (e) {
    this.setData({ examOrderText: e.detail.value });
  },

  saveExamOrders: function () {
    if (this.data.readOnly) return;
    const text = (this.data.examOrderText || '').trim();
    if (!text) {
      wx.showToast({ title: '请先填写医生检查单项目', icon: 'none' });
      return;
    }
    const exams = text.split(/[、,，;；\n]/).map(function (item) { return item.trim(); }).filter(Boolean);
    const self = this;
    api.journeyOrders(this.data.sessionId, exams).then(function (res) {
      self.setData({ card: res.card, state: res.state, step: res.step, examOrderText: (res.state.exams || []).join('、') });
      self.applyStepPlace(res.step);
      wx.showToast({ title: '已按医生检查单更新', icon: 'none' });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  nextStep: function () {
    if (this.data.readOnly || (this.data.step && this.data.step.index + 1 >= this.data.step.total)) return;
    const self = this;
    api.journeyStep(this.data.sessionId, 'next').then(function (res) {
      self.setData({ step: res.step, state: res.state });
      self.applyStepPlace(res.step);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  prevStep: function () {
    if (this.data.readOnly) return;
    const self = this;
    api.journeyStep(this.data.sessionId, 'back').then(function (res) {
      self.setData({ step: res.step, state: res.state });
      self.applyStepPlace(res.step);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  finishJourney: function () {
    if (this.data.readOnly) return;
    const self = this;
    api.journeyStep(this.data.sessionId, 'finish').then(function (res) {
      self.setData({
        step: res.step,
        state: res.state,
        readOnly: true,
        showCompleteModal: true
      });
      self.applyStepPlace(res.step);
    }).catch(function (err) {
      req.showError(err);
    });
  },

  closeCompleteModal: function () {
    this.setData({ showCompleteModal: false });
  },

  stopModalTap: function () {},

  goMyRecords: function () {
    this.setData({ showCompleteModal: false });
    wx.switchTab({ url: '/pages/my/my' });
  },

  goNavigate: function () {
    const target = this.data.placeTarget;
    if (!target) return;
    // 找到上一步的终点作为导航起点（使用 nav_target 而非 nav_label，因为后端用 nav_target 匹配 POI）
    const step = this.data.step;
    let startTarget = '';
    if (step && step.index > 0 && this.data.card) {
      const prevItem = this.data.card.steps[step.index - 1];
      if (prevItem && !prevItem.nav_target && (prevItem.key === 'exam' || prevItem.key === 'report')) {
        wx.showToast({ title: '请先按医生检查单完成检查流程', icon: 'none' });
        return;
      }
      if (prevItem && prevItem.nav_target) {
        startTarget = prevItem.nav_target;
        // 解析占位符 @dept 为实际科室名称
        if (startTarget === '@dept' && this.data.card.dept) {
          startTarget = this.data.card.dept.name;
        }
        // @exam 在后端已按医生检查单解析；未解析时不应猜测地点。
        if (startTarget === '@exam') startTarget = '';
      }
    }
    getApp().globalData.navTarget = target;
    getApp().globalData.navStartTarget = startTarget;
    wx.switchTab({ url: '/pages/navigate/navigate' });
  },

  goChat: function () {
    // 确保 globalData 中有完整的科室信息
    const deptId = this.data.deptId;
    if (deptId && !getApp().globalData.currentDept) {
      const self = this;
      api.department(deptId).then(function (dept) {
        getApp().globalData.currentDept = dept;
        wx.switchTab({ url: '/pages/chat/chat' });
      }).catch(function () {
        // 即使获取失败也跳转，chat 页面会自行恢复
        getApp().globalData.currentDept = { id: deptId };
        wx.switchTab({ url: '/pages/chat/chat' });
      });
    } else {
      wx.switchTab({ url: '/pages/chat/chat' });
    }
  }
});
