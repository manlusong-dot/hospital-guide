const api = require('../../utils/api');
const req = require('../../utils/request');

// 根据就诊步骤 key 返回对应的快捷标签
var STEP_CHIPS = {
  triage: ['我牙疼', '孩子发烧咳嗽', '头晕血压高', '肚子疼'],
  prep: ['需要空腹吗', '要带什么证件', '抽血前注意什么'],
  register: ['怎么挂号', '能用医保吗', '没有就诊卡怎么办'],
  checkin: ['在哪里签到', '还要等多久', '候诊区在哪'],
  first_visit: ['怎么跟医生说', '要做哪些检查', '下一步'],
  pay: ['怎么缴费', '能用手机支付吗', '医保怎么报'],
  exam: ['抽血要空腹吗', 'B超要憋尿吗', '报告多久出来'],
  report: ['报告出来了吗', '去哪取报告', '自助机在哪'],
  second_visit: ['报告给医生看', '需要重新挂号吗', '下一步'],
  final: ['诊断结果是什么', '要吃什么药', '需要复诊吗'],
  medicine: ['药怎么吃', '一天吃几次', '有什么副作用'],
  followup: ['什么时候复诊', '复诊要带什么', '病情变化怎么办']
};
var DEFAULT_CHIPS = ['我牙疼', '孩子发烧咳嗽', '头晕血压高', '下一步', '药怎么吃'];

function getChipsForStep(step) {
  if (!step || !step.key) return DEFAULT_CHIPS;
  return STEP_CHIPS[step.key] || DEFAULT_CHIPS;
}

Page({
  data: {
    mode: 'chat',
    messages: [],
    inputText: '',
    symptomText: '',
    triageResult: null,
    loading: false,
    quickChips: DEFAULT_CHIPS,
    lastStep: null,
    lastDeptId: '',
    showHistory: false,
    historyList: []
  },

  onLoad: function () {
    // 如果 globalData 中已有 session，说明是从其他页面返回，恢复状态
    const session = getApp().globalData.sessionId;
    const dept = getApp().globalData.currentDept;
    if (session && dept) {
      this.setData({
        lastDeptId: dept.id,
        messages: [{
          role: 'assistant',
          text: '您好, 我是就医陪伴助手。您正在' + dept.name + '就诊中，有什么需要帮忙的吗？'
        }]
      });
      // 恢复当前步骤进度
      api.journeyState(session).then(function (res) {
        this.setData({ lastStep: res.step || null, quickChips: getChipsForStep(res.step) });
      }.bind(this)).catch(function () {});
    } else {
      this.setData({
        messages: [{
          role: 'assistant',
          text: '您好, 我是就医陪伴助手。您可以跟我说说哪里不舒服, 我帮您选科室、安排看病流程。'
        }]
      });
    }
  },

  onShow: function () {
    // 从其他页面返回时，刷新科室和步骤状态
    const session = getApp().globalData.sessionId;
    const dept = getApp().globalData.currentDept;
    if (session && dept) {
      this.setData({ lastDeptId: dept.id });
      api.journeyState(session).then(function (res) {
        this.setData({ lastStep: res.step || null, quickChips: getChipsForStep(res.step) });
      }.bind(this)).catch(function () {});
    }
  },

  switchMode: function (e) {
    this.setData({ mode: e.currentTarget.dataset.mode });
  },

  onSymptomInput: function (e) {
    this.setData({ symptomText: e.detail.value });
  },

  startTriage: function () {
    const self = this;
    const text = this.data.symptomText.trim();
    if (!text) {
      wx.showToast({ title: '请先说说哪里不舒服', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    api.triage(text).then(function (res) {
      self.setData({ loading: false, triageResult: res });
    }).catch(function (err) {
      self.setData({ loading: false });
      req.showError(err);
    });
  },

  pickAlternative: function (e) {
    const dept = this.data.triageResult.alternatives[e.currentTarget.dataset.index];
    const result = this.data.triageResult;
    result.alternatives = (result.dept ? [result.dept] : []).concat(result.alternatives.filter(function (d) { return d && d.id !== dept.id; }));
    result.dept = dept;
    result.suggestion = '已改为' + dept.name + '(在' + dept.floor + '楼)';
    this.setData({ triageResult: result });
  },

  pickCandidate: function (e) {
    const candidate = this.data.triageResult.candidates[e.currentTarget.dataset.index];
    if (!candidate) return;
    const result = this.data.triageResult;
    result.dept = candidate;
    result.suggestion = '已选择' + candidate.name + '(在' + candidate.floor + '楼)';
    result.status = 'manual_selected';
    result.confidence = 'manual';
    this.setData({ triageResult: result });
  },

  goNavigateToDept: function () {
    const dept = this.data.triageResult.dept;
    if (!dept) {
      wx.showToast({ title: '请先选择一个候选科室', icon: 'none' });
      return;
    }
    getApp().globalData.currentDept = dept;
    getApp().globalData.navTarget = dept.name;
    getApp().globalData.navStartTarget = '主入口';
    wx.switchTab({ url: '/pages/navigate/navigate' });
  },

  makeJourneyCard: function () {
    const self = this;
    const dept = this.data.triageResult.dept;
    if (!dept) {
      wx.showToast({ title: '请先选择一个候选科室', icon: 'none' });
      return;
    }
    getApp().globalData.currentDept = dept;
    api.journeySession(null, dept.id).then(function (res) {
      getApp().globalData.sessionId = res.session_id;
      wx.navigateTo({ url: '/pages/journey/journey?session=' + res.session_id + '&dept=' + dept.id });
    }).catch(function (err) {
      req.showError(err);
    });
  },

  onChatInput: function (e) {
    this.setData({ inputText: e.detail.value });
  },

  tapChip: function (e) {
    this.sendMessage(e.currentTarget.dataset.text);
  },

  sendCurrent: function () {
    const text = this.data.inputText.trim();
    if (!text) return;
    this.setData({ inputText: '' });
    this.sendMessage(text);
  },

  sendMessage: function (text) {
    const self = this;
    const messages = this.data.messages.concat([{ role: 'user', text: text }]);
    this.setData({ messages: messages, loading: true });
    api.chat(getApp().globalData.sessionId || null, text, getApp().globalData.currentDept ? getApp().globalData.currentDept.id : null)
      .then(function (res) {
        if (res.session_id) {
          getApp().globalData.sessionId = res.session_id;
        }
        // 保存科室ID到data，避免异步问题
        const deptId = (res.state && res.state.dept_id) || '';
        // is_question 为 true 时不显示步骤进度条
        const showStepBar = !res.is_question;
        const updateData = {
          messages: messages.concat([{ role: 'assistant', text: res.reply, navigation: res.navigation || null }]),
          loading: false,
          lastStep: showStepBar ? (res.step || null) : self.data.lastStep,
          lastDeptId: deptId,
          quickChips: getChipsForStep(res.step)
        };

        // 同步更新科室信息
        if (deptId && !getApp().globalData.currentDept) {
          api.department(deptId).then(function (dept) {
            getApp().globalData.currentDept = dept;
          }).catch(function () {});
        }

        self.setData(updateData);
      }).catch(function (err) {
        self.setData({ loading: false });
        req.showError(err);
      });
  },

  goMessageNavigate: function (e) {
    const item = this.data.messages[e.currentTarget.dataset.index];
    const nav = item && item.navigation;
    if (!nav || !nav.target) return;
    getApp().globalData.navTarget = { ref: nav.target, label: nav.label || nav.target };
    getApp().globalData.navStartTarget = nav.start || '主入口';
    wx.switchTab({ url: '/pages/navigate/navigate' });
  },

  nextStep: function () {
    if (this.data.loading) return;
    this.sendMessage('下一步');
  },

  goJourney: function () {
    const self = this;
    const session = getApp().globalData.sessionId;
    const deptId = this.data.lastDeptId || (getApp().globalData.currentDept ? getApp().globalData.currentDept.id : '');

    // 如果有 session 但没有科室信息，尝试从后端恢复
    if (session && !deptId) {
      wx.showLoading({ title: '加载中...' });
      api.journeyState(session).then(function (res) {
        wx.hideLoading();
        const recoveredDeptId = res.state && res.state.dept_id;
        if (recoveredDeptId) {
          self.setData({ lastDeptId: recoveredDeptId });
          return api.department(recoveredDeptId).then(function (dept) {
            getApp().globalData.currentDept = dept;
            wx.navigateTo({ url: '/pages/journey/journey?session=' + session + '&dept=' + dept.id });
          });
        } else {
          wx.showToast({ title: '请先描述症状或选择科室', icon: 'none' });
        }
      }).catch(function () {
        wx.hideLoading();
        wx.showToast({ title: '加载失败，请重试', icon: 'none' });
      });
      return;
    }

    // 如果有 session 和科室信息，直接跳转
    if (session && deptId) {
      // 确保 globalData 中有科室信息
      if (!getApp().globalData.currentDept) {
        api.department(deptId).then(function (dept) {
          getApp().globalData.currentDept = dept;
          wx.navigateTo({ url: '/pages/journey/journey?session=' + session + '&dept=' + dept.id });
        }).catch(function () {
          wx.showToast({ title: '加载科室信息失败', icon: 'none' });
        });
      } else {
        wx.navigateTo({ url: '/pages/journey/journey?session=' + session + '&dept=' + deptId });
      }
    } else if (this.data.triageResult && this.data.triageResult.dept) {
      // 有导诊结果但还没生成 session，先生成
      const d = this.data.triageResult.dept;
      getApp().globalData.currentDept = d;
      api.journeySession(null, d.id).then(function (res) {
        getApp().globalData.sessionId = res.session_id;
        wx.navigateTo({ url: '/pages/journey/journey?session=' + res.session_id + '&dept=' + d.id });
      }).catch(function (err) {
        req.showError(err);
      });
    } else {
      wx.showToast({ title: '请先描述症状或选择科室', icon: 'none' });
    }
  },

  showHistory: function () {
    const self = this;
    wx.showLoading({ title: '加载中...' });
    api.chatSessions().then(function (list) {
      wx.hideLoading();
      self.setData({ showHistory: true, historyList: list });
    }).catch(function () {
      wx.hideLoading();
      wx.showToast({ title: '加载失败', icon: 'none' });
    });
  },

  hideHistory: function () {
    this.setData({ showHistory: false });
  },

  pickHistory: function (e) {
    const item = this.data.historyList[e.currentTarget.dataset.index];
    getApp().globalData.sessionId = item.session_id;
    // 清除当前对话，用新 session 重新加载
    this.setData({
      showHistory: false,
      messages: [],
      lastStep: null
    });
    // 重新加载该 session 的状态
    const self = this;
    api.journeyState(item.session_id).then(function (res) {
      if (res.state && res.state.dept_id) {
        api.department(res.state.dept_id).then(function (dept) {
          getApp().globalData.currentDept = dept;
          self.setData({
            lastDeptId: dept.id,
            messages: [{
              role: 'assistant',
              text: '您好, 这是您之前在' + dept.name + '的就诊记录，有什么需要帮忙的吗？'
            }],
            lastStep: res.step || null,
            quickChips: getChipsForStep(res.step)
          });
        }).catch(function () {
          self.setData({
            messages: [{
              role: 'assistant',
              text: '已切换到该就诊记录，有什么需要帮忙的吗？'
            }],
            lastStep: res.step || null,
            quickChips: getChipsForStep(res.step)
          });
        });
      }
    }).catch(function () {});
  },

  startNewVisit: function () {
    // 开始新的就诊：清除当前 session
    getApp().globalData.sessionId = '';
    getApp().globalData.currentDept = null;
    this.setData({
      showHistory: false,
      messages: [{
        role: 'assistant',
        text: '您好, 我是就医陪伴助手。您可以跟我说说哪里不舒服, 我帮您选科室、安排看病流程。'
      }],
      lastStep: null,
      lastDeptId: '',
      quickChips: DEFAULT_CHIPS
    });
  }
});
