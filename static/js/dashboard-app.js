const { createApp, computed } = Vue;

      // =================================================================
      // ⚠️  Vue 3 命名约定（无构建步骤时务必遵守）
      //
      //  1. methods / computed 中的方法名 **不得以 _ 开头**。
      //     Vue 3 模板编译器将 _xxx 保留为内部 helper 命名空间
      //     （_createVNode / _openBlock 等），模板里调用 _xxx() 会在
      //     运行时静默解析为 undefined()，导致组件白屏。
      //     "私有"辅助方法请使用 prvXxx 形式命名。
      //
      //  2. 模板表达式只能引用 data / computed / methods 中定义的名称；
      //     全局变量须挂到 app.config.globalProperties 或 provide/inject。
      //
      //  3. 如需更严格的编译期检查，考虑迁移到 Vite + Vue SFC + TypeScript。
      // =================================================================

      // ---------------------------------------------------------
      // 产品化配置映射 (Business Data Layer)
      // ---------------------------------------------------------

      const FIELD_DICTIONARY = {
        // Platform & Visual
        "platform": {
          label: "发布平台",
          type: "select",
          options: [
            { value: "bilibili_landscape", label: "📺 哔哩哔哩-横屏 (1920x1080)" },
            { value: "douyin", label: "🎵 抖音/TikTok-竖屏 (1080x1920)" },
            { value: "xiaohongshu", label: "📕 小红书-竖屏 (1080x1350)" },
            { value: "bilibili_vertical", label: "📱 哔哩哔哩-竖屏 (1080x1920)" }
          ],
          tip: "不同平台会自动适配相应的分辨率和安全区"
        },
        "style": {
          label: "内容风格",
          type: "select",
          options: [
            { value: "tech", label: "科技感 / 数据理性" },
            { value: "minimal", label: "极简 / 清爽" },
            { value: "news", label: "新闻播报 / 强信息" },
            { value: "trendy", label: "潮流 / 抓眼" },
            { value: "cinematic", label: "电影感（内部映射）" },
            { value: "dramatic", label: "戏剧张力（内部映射）" }
          ],
          default: "tech"
        },
        "quality": {
          label: "渲染质量",
          type: "select",
          options: [
            { value: "preview", label: "🟢 快速预览 (低清/低帧率/生成快)" },
            { value: "draft", label: "🟡 草稿模式 (高清/标准帧率)" },
            { value: "final", label: "🔴 最终交付 (超清/60FPS/高码率)" }
          ],
          default: "preview"
        },
        "topic": { label: "视频主题", placeholder: "例如：房贷利息真相", tip: "用于生成剧本主题，可为空" },
        "output_file": { label: "文件名称", placeholder: "自动命名 (推荐)", tip: "留空则自动生成带时间戳的文件名" },
        "video_duration": { label: "视频时长", unit: "秒" },
        "duration": { label: "目标时长", unit: "秒" },
        "fps": { label: "帧率 FPS", advanced: true },
        "width": { label: "宽度 px", advanced: true },
        "height": { label: "高度 px", advanced: true },
        "dpi": { label: "DPI", advanced: true },
        "bitrate": { label: "码率", advanced: true },
        "preset": { label: "编码预设", advanced: true },
        "crf": { label: "CRF", advanced: true },
        "burn_subtitles": { label: "烧录字幕", type: "bool", default: true, tip: "是否将字幕直接渲染进视频画面" },

        // Business Logic (Loan)
        "loan_amount": { label: "贷款总额", unit: "元", default: 1000000 },
        "annual_rate": { label: "年利率", unit: "小数 (如0.045)", default: 0.045, tip: "输入小数，例如 4.5% 请输入 0.045" },
        "loan_years": { label: "贷款年限", unit: "年", default: 30 },

        // Business Logic (Fund)
        "principal": { label: "初始本金", unit: "元", default: 100000 },
        "gross_return": { label: "预期年化收益", unit: "小数", default: 0.08, tip: "输入小数，例如 8% 请输入 0.08" },
        "years": { label: "投资时长", unit: "年", default: 20 },
      };

      const TASK_FRIENDLY_NAMES = {
        "loan_comparison": "房贷计算可视化",
        "fund_fee_erosion": "基金复利可视化",
        "video_platform_introduction": "平台介绍视频",
        "smoke_check": "环境自检",
        "scene_schedule_preview": "节拍预览",
        "loan_animation": "生成视频",
        "fund_animation": "生成视频",
        "generate_intro_video": "生成平台介绍视频",
        "render": "生成视频"
      };

      const HIDDEN_TASKS = new Set(['api']);

      const TASK_LANE_META = {
        prep: {
          label: '准备',
          icon: 'bi bi-check2-circle',
        },
        core: {
          label: '创作',
          icon: 'bi bi-film',
        },
      };

      // ---------------------------------------------------------
      // App Logic
      // ---------------------------------------------------------

      createApp({
        data() {
          return {
            projects: [],
            /** 侧栏项目列表：搜索与排序 */
            projectListQuery: '',
            projectListSort: 'name_asc',
            currentProject: null,
            currentTask: null,
            taskDetails: {},
            taskParams: [],
            formValues: {},
            logs: [],
            loadingProjects: false,
            loadingTask: false,
            running: false,
            error: null,
            showAdvanced: false,
            taskSuccess: false,
            currentJobResult: null,
            /** 最近一次失败（闭环展示） */
            lastFailure: null,
            lastJobId: null,
            /** 仅收起「任务结果验收」横幅，不清理 currentJobResult（节拍表仍可查看） */
            outcomeBannerDismissed: false,
            showSceneLogs: false,
            expandedSceneKey: null,

            screenplaySession: {
              providers: [],
              provider: '',
              providerUsed: '',
              fallbackUsed: false,
              screenplay: null,
              dirtySceneIds: [],
              previewLoading: false,
              saveLoading: false,
              error: null,
              generatedAt: null,
            },
            screenplayJsonDraft: '',
            screenplayAttachError: null,
            /** 仅当为 true 时，允许在成片任务下不带 Screenplay 运行（默认 false，避免误提交空剧本） */
            allowRunWithoutScreenplay: false,

            // Create Project State
            newProject: { name: '', description: '' },
            creatingProject: false,
            createError: null,
            bsModal: null,

            // Delete Project State
            deleteTarget: { name: '', displayName: '' },
            deleteConfirmInput: '',
            deleteAckDanger: false,
            deleteError: null,
            deletingProject: false,
            bsDeleteModal: null,

            // Settings State
            settings: {},
            settingsLoading: false,
            bsSettingsModal: null,
            bsGuideModal: null,

            /** 侧栏一级分区：projects | agent（与 README / 使用说明一致） */
            sidebarPrimaryTab: 'projects',

            /** Studio 意图会话（/api/v1/sessions） */
            studioSessions: [],
            selectedStudioSessionId: null,
            studioSessionDetail: null,
            studioSessionsLoading: false,
            studioSessionDetailLoading: false,
            studioSessionsError: null,
            /** 会话列表 404 等：中性说明，避免默认红字「404」惊吓 */
            studioSessionsSoftNotice: null,
            /** 编辑会话标题的临时状态 */
            editingSessionId: null,
            editingSessionTitle: '',
            deleteConfirmSessionId: null,

            // ── AI Agent Panel State ──
            agentPrompt: '',
            agentCompiling: false,
            agentCompileError: null,
            agentCompiledResult: null,   // StandardVideoJobRequest 编译结果
            agentEditedKwargs: {},       // 用户可编辑的 kwargs 副本
            agentLinkedSessionId: null,  // 当前编译关联的会话 ID
            agentRunning: false,
            agentJobId: null,
            agentJobSuccess: false,
            agentJobFailure: null,
            agentJobResult: null,
            agentLogs: [],

            // ── Code Studio State ──
            csSelectedProjectName: '',
            csSelectedTaskName: '',      // 当前选中的任务，空字符串表示未选
            csSessions: [],
            csSessionsLoading: false,
            csSessionsError: null,
            csSelectedSessionId: null,
            csSessionDetail: null,
            csSessionDetailLoading: false,
            csPrompt: '',
            csFileHint: '',
            csCompiling: false,
            csCompileError: null,
            csLatestPatch: null,         // { file_path, new_content, explanation, turn_id }
            csLatestPatchApplied: false,
            csApplying: false,
            csApplyError: null,
            csApplySuccess: null,

            // ── Viz Backends State ──
            vizBackends: [],
          }
        },
        computed: {
          commonParams() {
            return this.taskParams.filter(p => !this.isAdvanced(p.name) && !this.isHiddenField(p.name));
          },
          advancedParams() {
            return this.taskParams.filter(p => this.isAdvanced(p.name) && !this.isHiddenField(p.name));
          },
          requiredParamsCount() {
            return this.taskParams.filter(p => p.required && !this.isHiddenField(p.name)).length;
          },
          isFormValid() {
            return this.taskParams.filter(p => !this.isHiddenField(p.name)).every(p => {
              if(!p.required) return true;
              return !this.isEmpty(this.formValues[p.name]);
            });
          },
          /** 成片任务默认要求已加载剧本，除非用户显式勾选「不使用剧本」 */
          canStartRun() {
            if (!this.isFormValid) return false;
            if (!this.canAttachScreenplay()) return true;
            if (this.screenplaySession.screenplay) return true;
            return this.allowRunWithoutScreenplay === true;
          },
          currentSceneSchedule() {
            return this.currentJobResult && this.currentJobResult.scene_schedule ? this.currentJobResult.scene_schedule : null;
          },
          /** idle | running | success | failed */
          runPhase() {
            if (this.running) return 'running';
            if (this.taskSuccess) return 'success';
            if (this.lastFailure) return 'failed';
            return 'idle';
          },
          showOutcomePanel() {
            return !!(
              this.currentTask &&
              !this.running &&
              (this.taskSuccess || this.lastFailure) &&
              !this.outcomeBannerDismissed
            );
          },
          workflowKindLabel() {
            if (!this.currentTask) return '工作流程';
            const n = this.currentTask.name;
            if (n === 'smoke_check' || n === 'scene_schedule_preview') return '项目检查';
            if (n === 'render' || n.endsWith('animation') || n.endsWith('video')) return '视频创作';
            return '任务执行';
          },
          workflowSteps() {
            if (!this.currentTask) return [];
            const rp = this.runPhase;
            const prep = this.canStartRun;
            return [
              { id: 'w1', title: '配置', hint: '设置参数与内容', done: prep, active: !prep && rp === 'idle' },
              {
                id: 'w2',
                title: '生成',
                hint: rp === 'running' ? '渲染中…' : '点击开始运行',
                done: rp === 'success' || rp === 'failed',
                active: rp === 'running' || (prep && rp === 'idle'),
              },
              {
                id: 'w3',
                title: '完成',
                hint: rp === 'failed' ? '查看错误并重试' : '查看成果',
                done: rp === 'success' || rp === 'failed',
                active: rp === 'success' || rp === 'failed',
                failed: rp === 'failed',
              },
            ];
          },
          jobArtifacts() {
            if (!this.currentJobResult || typeof this.currentJobResult !== 'object') return [];
            return this.extractArtifactsFromResult(this.currentJobResult);
          },
          /** Self-correction report from a successful job (retries happened) */
          jobSelfCorrection() {
            if (!this.currentJobResult || typeof this.currentJobResult !== 'object') return null;
            return this.currentJobResult.self_correction || null;
          },
          canConfirmDelete() {
            return !!(
              this.deleteAckDanger &&
              this.deleteTarget &&
              this.deleteTarget.name &&
              this.deleteConfirmInput === this.deleteTarget.name
            );
          },
          /** 筛选 + 排序后的项目（侧栏列表数据源） */
          filteredSortedProjects() {
            const q = (this.projectListQuery || '').trim().toLowerCase();
            let list = [...(this.projects || [])];
            if (q) {
              list = list.filter((p) => {
                const disp = String(this.getProjectDisplayName(p) || '').toLowerCase();
                const name = String(p.name || '').toLowerCase();
                const desc = String(p.description || '').toLowerCase();
                return name.includes(q) || disp.includes(q) || desc.includes(q);
              });
            }
            const sort = this.projectListSort;
            list.sort((a, b) => {
              if (sort === 'name_desc') {
                return b.name.localeCompare(a.name, 'zh-CN');
              }
              if (sort === 'display_asc') {
                const da = this.getProjectDisplayName(a);
                const db = this.getProjectDisplayName(b);
                return da.localeCompare(db, 'zh-CN');
              }
              return a.name.localeCompare(b.name, 'zh-CN');
            });
            return list;
          },
          isCurrentProjectInFilter() {
            if (!this.currentProject) return true;
            return this.filteredSortedProjects.some((p) => p.name === this.currentProject);
          },
          /** 随侧栏分区切换的简短提示，与「使用说明」模态框叙事一致 */
          sidebarTabHint() {
            if (this.sidebarPrimaryTab === 'agent') {
              return 'AI 对话与历史记录';
            }
            if (this.sidebarPrimaryTab === 'code-studio') {
              return '用自然语言修改渲染代码';
            }
            return '选择项目，点击任务开始工作';
          },
          agentMode() {
            return this.sidebarPrimaryTab === 'agent';
          },
          codeStudioMode() {
            return this.sidebarPrimaryTab === 'code-studio';
          },
          /** 当前选中项目的任务列表（供代码工坊任务下拉使用） */
          csTasksForSelectedProject() {
            const proj = this.projects.find(p => p.name === this.csSelectedProjectName);
            return (proj && proj.tasks) ? proj.tasks.filter(t => !HIDDEN_TASKS.has(t.name)) : [];
          },
          /** 各 Tab 是否有任务进行中（用于跨 Tab 提示） */
          projectsTabBusy() {
            return this.running === true;
          },
          agentTabBusy() {
            return this.agentCompiling || this.agentRunning;
          },
          codeStudioTabBusy() {
            return this.csCompiling || this.csApplying;
          },
          agentAiConfigured() {
            const s = this.settings;
            return !!(s && s.openai_base_url && s.openai_api_key && s.openai_model);
          },
          /** 是否已有进行中（未完成）的意图会话，有则禁止再新建 */
          hasActiveStudioSession() {
            return this.studioSessions.some(s => s.is_completed === false);
          },
        },
        mounted() {
          this.fetchProjects();
          this.fetchSettings();
          this.fetchVizBackends();
          // 仅在「意图会话」分区加载列表，避免默认停在「项目与任务」时仍请求 /api/v1/sessions 并显示 Not Found
          if (this.sidebarPrimaryTab === 'agent') {
            this.fetchStudioSessions();
          }
          this.addLog("控制台就绪。请选择任务开始。");
          const modalEl = document.getElementById('createProjectModal');
          if (modalEl) {
             this.bsModal = new bootstrap.Modal(modalEl);
          }
          const settingsModalEl = document.getElementById('settingsModal');
          if (settingsModalEl) {
             this.bsSettingsModal = new bootstrap.Modal(settingsModalEl);
          }
          const deleteModalEl = document.getElementById('deleteProjectModal');
          if (deleteModalEl) {
            this.bsDeleteModal = new bootstrap.Modal(deleteModalEl);
          }
          const guideModalEl = document.getElementById('guideModal');
          if (guideModalEl) {
            this.bsGuideModal = new bootstrap.Modal(guideModalEl);
          }
          try {
            const saved = localStorage.getItem('video_dashboard_project_sort');
            if (saved && ['name_asc', 'name_desc', 'display_asc'].includes(saved)) {
              this.projectListSort = saved;
            }
          } catch (e) { /* ignore */ }
          try {
            const tab = localStorage.getItem('video_dashboard_sidebar_tab');
            if (tab === 'projects' || tab === 'agent' || tab === 'code-studio') {
              this.sidebarPrimaryTab = tab;
            }
          } catch (e) { /* ignore */ }
        },
        watch: {
          logs: {
            handler() {
              this.$nextTick(() => {
                const el = this.$refs.logWindow;
                if (el) el.scrollTop = el.scrollHeight;
              });
            },
            deep: true
          },
          projectListSort(val) {
            try {
              localStorage.setItem('video_dashboard_project_sort', val);
            } catch (e) { /* ignore */ }
          },
          sidebarPrimaryTab(val) {
            try {
              localStorage.setItem('video_dashboard_sidebar_tab', val);
            } catch (e) { /* ignore */ }
            if (val === 'projects') {
              this.studioSessionsError = null;
              this.studioSessionsSoftNotice = null;
            }
            if (val === 'agent') {
              this.fetchStudioSessions();
              this.fetchSettings();
            }
            if (val === 'code-studio') {
              this.fetchSettings();
              if (this.csSelectedProjectName) this.csFetchSessions();
            }
          },
        },
        methods: {
          taskLaneMeta(key) {
            return TASK_LANE_META[key] || TASK_LANE_META.other;
          },
          openGuideModal() {
            if (this.bsGuideModal) this.bsGuideModal.show();
          },
          prettyJson(obj) {
            if (obj == null) return '';
            try {
              return JSON.stringify(obj, null, 2);
            } catch (e) {
              return String(obj);
            }
          },
          studioSessionLabel(s) {
            if (!s || !s.id) return '';
            if (s.title && String(s.title).trim()) return String(s.title).trim();
            // 未完成的会话显示"当前会话"
            if (!s.is_completed) return '当前会话';
            // 已完成未命名会话：显示序号或id
            const idx = this.studioSessions.findIndex(x => x.id === s.id);
            if (idx !== -1) return `会话 ${this.studioSessions.length - idx}`;
            return s.id.slice(-6);
          },
          formatStudioTime(iso) {
            if (!iso) return '';
            try {
              const d = new Date(iso);
              return d.toLocaleString('zh-CN', { hour12: false });
            } catch (e) {
              return iso;
            }
          },
          _apiErrorMessage(data, fallback) {
            const d = data && data.detail;
            if (typeof d === 'string') return d;
            if (Array.isArray(d)) return d.map((x) => (x && x.msg) || JSON.stringify(x)).join('; ');
            if (d && typeof d === 'object') return JSON.stringify(d);
            return fallback || '请求失败';
          },
          async fetchStudioSessions() {
            this.studioSessionsLoading = true;
            this.studioSessionsError = null;
            this.studioSessionsSoftNotice = null;
            try {
              const res = await fetch('/api/v1/sessions?limit=30');
              let data = {};
              try {
                data = await res.json();
              } catch (e) {
                data = {};
              }
              if (!res.ok) {
                if (res.status === 404) {
                  this.studioSessions = [];
                  this.studioSessionsSoftNotice =
                    '未检测到会话接口（HTTP 404）。未使用「意图会话」时可忽略；需要时请用本仓库启动 dashboard 并确认已挂载 /api/v1。';
                  return;
                }
                let msg = this._apiErrorMessage(data, res.statusText);
                throw new Error(msg);
              }
              this.studioSessions = data.items || [];
              // 刷新后检验当前选中会话是否仍在列表中，否则清除选中状态
              if (this.selectedStudioSessionId) {
                const stillExists = this.studioSessions.some(s => s.id === this.selectedStudioSessionId);
                if (!stillExists) {
                  this.selectedStudioSessionId = null;
                  this.studioSessionDetail = null;
                }
              }
            } catch (err) {
              this.studioSessionsError = err.message || String(err);
              this.studioSessions = [];
            } finally {
              this.studioSessionsLoading = false;
            }
          },
          async createStudioSession() {
            this.studioSessionsError = null;
            if (this.hasActiveStudioSession) {
              this.studioSessionsError = '已有一个进行中的会话，请等待当前会话完成后再创建新会话。';
              return;
            }
            try {
              const res = await fetch('/api/v1/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: null, meta: {} })
              });
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              await this.fetchStudioSessions();
              if (data.session_id) {
                await this.selectStudioSession(data.session_id);
              }
              this.addLog(`已创建意图会话：${data.session_id || '?'}`);
            } catch (err) {
              this.studioSessionsError = err.message || String(err);
            }
          },
          async selectStudioSession(id) {
            if (!id) return;
            this.selectedStudioSessionId = id;
            this.studioSessionDetailLoading = true;
            this.studioSessionDetail = null;
            this.studioSessionsError = null;
            await this.refreshStudioSessionDetail();
          },
          async refreshStudioSessionDetail() {
            if (!this.selectedStudioSessionId) return;
            this.studioSessionDetailLoading = true;
            this.studioSessionsError = null;
            try {
              const res = await fetch(`/api/v1/sessions/${encodeURIComponent(this.selectedStudioSessionId)}`);
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              this.studioSessionDetail = data;
            } catch (err) {
              this.studioSessionsError = err.message || String(err);
              this.studioSessionDetail = null;
            } finally {
              this.studioSessionDetailLoading = false;
            }
          },
          openEditSessionTitle(sessionId, currentTitle) {
            this.editingSessionId = sessionId;
            this.editingSessionTitle = currentTitle || '';
            // TODO: 显示编辑模态框或内联编辑
            this.showEditSessionTitleDialog(sessionId, currentTitle);
          },
          showEditSessionTitleDialog(sessionId, currentTitle) {
            // 简单实现：使用 prompt
            const newTitle = prompt('输入新的会话标题（留空使用自动生成的标题）:', currentTitle || '');
            if (newTitle !== null) {
              this.updateSessionTitle(sessionId, newTitle.trim() || null);
            }
          },
          async updateSessionTitle(sessionId, newTitle) {
            try {
              const res = await fetch(`/api/v1/sessions/${encodeURIComponent(sessionId)}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle })
              });
              if (!res.ok) {
                const data = await res.json();
                throw new Error(this._apiErrorMessage(data, res.statusText));
              }
              await this.fetchStudioSessions();
              this.addLog(`已更新会话标题`);
              this.editingSessionId = null;
              this.editingSessionTitle = '';
            } catch (err) {
              this.studioSessionsError = err.message || String(err);
            }
          },
          confirmDeleteSession(sessionId) {
            const session = this.studioSessions.find(s => s.id === sessionId);
            // 防止删除进行中的会话
            if (session && !session.is_completed) {
              this.studioSessionsError = '进行中的会话无法删除，请等待编译完成后再尝试。';
              return;
            }
            const title = this.studioSessionLabel(session);
            if (confirm(`确定删除会话"${title}"吗？此操作不可撤销。`)) {
              this.deleteSession(sessionId);
            }
          },
          async deleteSession(sessionId) {
            try {
              const res = await fetch(`/api/v1/sessions/${encodeURIComponent(sessionId)}`, {
                method: 'DELETE'
              });
              if (!res.ok) {
                const data = await res.json();
                throw new Error(this._apiErrorMessage(data, res.statusText));
              }
              if (this.selectedStudioSessionId === sessionId) {
                this.clearStudioSessionSelection();
              }
              await this.fetchStudioSessions();
              this.addLog(`已删除会话`);
            } catch (err) {
              this.studioSessionsError = err.message || String(err);
            }
          },
          clearStudioSessionSelection() {
            this.selectedStudioSessionId = null;
            this.studioSessionDetail = null;
            this.deleteConfirmSessionId = null;
            // 切换会话时同步清除编译面板状态，避免旧会话的结果出现在新会话中
            // 保留 agentPrompt，方便用户在新会话中复用输入
            this.agentCompiledResult = null;
            this.agentEditedKwargs = {};
            this.agentCompileError = null;
            this.agentJobSuccess = false;
            this.agentJobFailure = null;
            this.agentJobResult = null;
            this.agentJobId = null;
            this.agentLogs = [];
            this.agentLinkedSessionId = null;
          },
          /** 批量清理所有未完成（残余）会话：先 complete 再 delete */
          async cleanupStaleSessions() {
            const stale = this.studioSessions.filter(s => s.is_completed === false);
            if (stale.length === 0) return;
            this.studioSessionsError = null;
            let cleaned = 0;
            for (const s of stale) {
              try {
                // 1. 标记已完成
                await fetch(`/api/v1/sessions/${encodeURIComponent(s.id)}/complete`, { method: 'POST' });
                // 2. 删除
                await fetch(`/api/v1/sessions/${encodeURIComponent(s.id)}`, { method: 'DELETE' });
                if (this.selectedStudioSessionId === s.id) this.clearStudioSessionSelection();
                cleaned++;
              } catch (e) {
                // 单条失败不中断
              }
            }
            await this.fetchStudioSessions();
            this.addLog(`已清理 ${cleaned} 个残余空会话`);
          },
          copyStudioTemplate(obj) {
            const text = this.prettyJson(obj);
            if (!text) return;
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(text).then(() => {
                this.addLog('已复制标准模板 JSON 到剪贴板');
              }).catch(() => {
                this.addLog('复制失败，请手动选择文本');
              });
            }
          },
          getFriendlyProjectName(name) {
             if (TASK_FRIENDLY_NAMES[name]) return TASK_FRIENDLY_NAMES[name];
             return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          },
          getFriendlyTaskName(name) {
             if (TASK_FRIENDLY_NAMES[name]) return TASK_FRIENDLY_NAMES[name];
             return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          },
          getProjectDisplayName(arg) {
             let name, desc;
             if (typeof arg === 'string') {
                name = arg;
                const p = this.projects.find(x => x.name === name);
                if (p) desc = p.description;
             } else if (arg) {
                name = arg.name;
                desc = arg.description;
             } else {
                return '';
             }

             if (TASK_FRIENDLY_NAMES[name]) return TASK_FRIENDLY_NAMES[name];
             if (desc && !desc.includes("data visualization project")) {
                 return desc;
             }
             return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
          },
          getTaskBrief(task) { return task.description || '无详细描述'; },

          openDeleteProjectModal(proj, ev) {
            if (ev && typeof ev.stopPropagation === 'function') ev.stopPropagation();
            if (!proj || proj.deletable === false) return;
            this.deleteTarget = { name: proj.name, displayName: this.getProjectDisplayName(proj) };
            this.deleteConfirmInput = '';
            this.deleteAckDanger = false;
            this.deleteError = null;
            if (this.bsDeleteModal) this.bsDeleteModal.show();
          },

          clearTaskSelection() {
            this.currentProject = null;
            this.currentTask = null;
            this.taskParams = [];
            this.formValues = {};
            this.taskDetails = {};
            this.loadingTask = false;
            this.taskSuccess = false;
            this.currentJobResult = null;
            this.lastFailure = null;
            this.lastJobId = null;
            this.outcomeBannerDismissed = false;
            this.showSceneLogs = false;
            this.expandedSceneKey = null;
            this.logs = [];
            this.resetScreenplaySession();
          },

          async confirmDeleteProject() {
            if (!this.canConfirmDelete || !this.deleteTarget.name) return;
            this.deletingProject = true;
            this.deleteError = null;
            const name = this.deleteTarget.name;
            try {
              // 使用 POST，与「新建项目」同为 POST，且避免部分环境下 DELETE 未注册（旧进程）返回 404 Not Found
              const res = await fetch('/api/projects/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name }),
              });
              const data = await res.json().catch(() => ({}));
              const detail = data.detail;
              const detailStr = Array.isArray(detail)
                ? detail.map((d) => (typeof d === 'object' && d.msg ? d.msg : JSON.stringify(d))).join('; ')
                : (detail || res.statusText || '删除失败');
              if (!res.ok) throw new Error(detailStr);
              this.addLog(`🗑️ 已删除项目目录：${name}`);
              if (this.bsDeleteModal) this.bsDeleteModal.hide();
              if (this.currentProject === name) this.clearTaskSelection();
              await this.fetchProjects();
            } catch (err) {
              this.deleteError = err.message || String(err);
              this.addLog(`❌ 删除项目失败: ${this.deleteError}`);
            } finally {
              this.deletingProject = false;
            }
          },

          getFieldConfig(name) { return FIELD_DICTIONARY[name] || {}; },
          getFieldLabel(name) { return this.getFieldConfig(name).label || name; },
          getFieldUnit(name) { return this.getFieldConfig(name).unit || ''; },
          getFieldTip(name) { return this.getFieldConfig(name).tip || ''; },
          getFieldType(name) { return this.getFieldConfig(name).type || 'text'; },
          getFieldOptions(name) { return this.getFieldConfig(name).options || []; },
          isAdvanced(name) { return !!this.getFieldConfig(name).advanced; },
          isHiddenField(name) { return ['screenplay'].includes(name); },
          getProjectMeta(projectName) {
            return this.projects.find(project => project.name === projectName) || null;
          },
          projectHasCapability(projectName, capabilityName) {
            const project = this.getProjectMeta(projectName);
            return !!(project && project.capabilities && project.capabilities[capabilityName]);
          },
          isPrimaryRenderTask(task) {
            return !!(task && (task.name === 'render' || task.name.endsWith('animation') || task.name.endsWith('video')));
          },
          supportsScreenplayWorkflow() {
            return this.projectHasCapability(this.currentProject, 'screenplay_workflow') && this.isPrimaryRenderTask(this.currentTask);
          },
          /** 成片类任务：可附加 Screenplay JSON，由调度器传入子进程（不依赖是否开通 AI 剧本能力） */
          canAttachScreenplay() {
            return this.isPrimaryRenderTask(this.currentTask);
          },

          isEmpty(val) { return val === null || val === undefined || val === ''; },

          getLogClass(msg) {
            if (msg.includes("Error") || msg.includes("Failed") || msg.includes("失败")) return "log-error";
            if (msg.includes("Success") || msg.includes("Finished") || msg.includes("成功")) return "log-success";
            return "log-info";
          },
          workflowStepClass(step) {
            if (step.state === 'warn') return 'is-warn';
            if (step.failed) return 'is-fail';
            if (step.done) return 'is-done';
            if (step.active) return 'is-active';
            return 'border-light bg-white';
          },
          extractArtifactsFromResult(obj) {
            const LABELS = {
              final_video_path: '成片视频',
              rendered_video_path: '渲染中间文件',
              scene_schedule_path: 'Scene 节拍 JSON',
              subtitle_path: '字幕 SRT',
              styled_subtitle_path: '样式字幕 ASS',
              cover_path: '封面图',
              render_manifest_path: 'Render Manifest',
            };
            const out = [];
            const seen = new Set();
            const tryPush = (k, v) => {
              if (typeof v !== 'string' || v.length < 4) return;
              if (!/[\\/]/.test(v)) return;
              if (!/\.(mp4|mov|mkv|json|srt|ass|png|jpg|webp|md)$/i.test(v)) return;
              if (seen.has(v)) return;
              seen.add(v);
              out.push({ key: k, label: LABELS[k] || k, path: v });
            };
            const walk = (o) => {
              if (!o || typeof o !== 'object') return;
              for (const [k, v] of Object.entries(o)) {
                if (k === 'scene_schedule' || k === 'job_id' || k === 'scene_schedule_download_url') continue;
                if (typeof v === 'string') tryPush(k, v);
                else if (typeof v === 'object' && v !== null && !Array.isArray(v)) walk(v);
              }
            };
            walk(obj);
            return out;
          },
          copyText(text) {
            if (!text) return;
            navigator.clipboard.writeText(text).then(() => {
              this.addLog('📋 已复制到剪贴板');
            }).catch(() => {
              this.addLog('❌ 复制失败，请手动选择路径文本');
            });
          },
          dismissOutcome() {
            this.outcomeBannerDismissed = true;
            this.addLog('已收起验收横幅；节拍表与日志仍保留。再次运行任务将重新显示验收区。');
          },
          retryLastRun() {
            this.runTask();
          },
            formatScheduleSeconds(value) {
              if (value === null || value === undefined || value === '') return '-';
              return `${Number(value).toFixed(2)}s`;
            },
              scheduleSceneKey(scene) {
                return `${scene.scene_id || 'scene'}-${scene.start_frame || 0}-${scene.end_frame || 0}`;
              },
              toggleSceneDetail(scene) {
                const key = this.scheduleSceneKey(scene);
                this.expandedSceneKey = this.expandedSceneKey === key ? null : key;
              },
              sceneDurationLabel(scene) {
                if (scene.duration_seconds !== undefined && scene.duration_seconds !== null) {
                  return this.formatScheduleSeconds(scene.duration_seconds);
                }
                const start = Number(scene.start_seconds || 0);
                const end = Number(scene.end_seconds || 0);
                return this.formatScheduleSeconds(Math.max(0, end - start));
              },
              phaseBadgeClass(role) {
                if (role === 'intro') return 'schedule-phase-intro';
                if (role === 'conclusion') return 'schedule-phase-conclusion';
                return 'schedule-phase-main';
              },
          addLog(msg) {
            const now = new Date();
            const ts = now.getHours().toString().padStart(2,'0') + ':' +
                       now.getMinutes().toString().padStart(2,'0') + ':' +
                       now.getSeconds().toString().padStart(2,'0');
            this.logs.push({ ts, msg });
          },
          resetScreenplaySession() {
            this.screenplaySession = {
              providers: [],
              provider: '',
              providerUsed: '',
              fallbackUsed: false,
              screenplay: null,
              dirtySceneIds: [],
              previewLoading: false,
              saveLoading: false,
              error: null,
              generatedAt: null,
            };
            this.screenplayJsonDraft = '';
            this.screenplayAttachError = null;
            this.allowRunWithoutScreenplay = false;
          },
          applyScreenplayObject(obj, sourceLabel) {
            if (!obj || typeof obj !== 'object') throw new Error('剧本必须是 JSON 对象');
            if (!Array.isArray(obj.scenes) || obj.scenes.length === 0) throw new Error('缺少 scenes 数组或为空');
            if (!obj.title) throw new Error('缺少 title');
            this.screenplaySession.screenplay = obj;
            this.screenplaySession.generatedAt = sourceLabel || new Date().toLocaleString('zh-CN');
            this.screenplaySession.providerUsed = 'json_import';
            this.screenplaySession.fallbackUsed = false;
            this.screenplayAttachError = null;
            this.allowRunWithoutScreenplay = false;
            this.addLog(`📎 已加载剧本：${obj.title}（${obj.scenes.length} 个 scene）`);
          },
          applyScreenplayJsonFromDraft() {
            this.screenplayAttachError = null;
            try {
              const raw = (this.screenplayJsonDraft || '').trim();
              if (!raw) {
                throw new Error('请粘贴 JSON 或先点击「加载示例到编辑区」');
              }
              const obj = JSON.parse(raw);
              this.applyScreenplayObject(obj, '手动粘贴 JSON');
            } catch (err) {
              this.screenplayAttachError = err.message || String(err);
              this.addLog(`❌ 剧本 JSON 解析失败: ${this.screenplayAttachError}`);
            }
          },
          loadSampleScreenplayToDraft() {
            this.screenplayAttachError = null;
            fetch('/static/sample_screenplay.json')
              .then(r => { if (!r.ok) throw new Error('无法加载示例文件'); return r.json(); })
              .then(j => { this.screenplayJsonDraft = JSON.stringify(j, null, 2); this.addLog('已载入示例剧本到编辑区，可修改后点击「解析并加载」。'); })
              .catch(e => { this.screenplayAttachError = e.message; });
          },
          onScreenplayFileChange(ev) {
            const f = ev.target.files && ev.target.files[0];
            this.screenplayAttachError = null;
            if (!f) return;
            const reader = new FileReader();
            reader.onload = () => {
              try {
                const text = String(reader.result || '');
                this.screenplayJsonDraft = text;
                const obj = JSON.parse(text);
                this.applyScreenplayObject(obj, `文件：${f.name}`);
              } catch (err) {
                this.screenplayAttachError = err.message || String(err);
                this.addLog(`❌ 剧本文件解析失败: ${this.screenplayAttachError}`);
              }
            };
            reader.readAsText(f, 'UTF-8');
            ev.target.value = '';
          },
          clearAttachedScreenplay() {
            this.screenplaySession.screenplay = null;
            this.screenplayJsonDraft = '';
            this.screenplayAttachError = null;
            this.allowRunWithoutScreenplay = false;
            this.addLog('已清除已加载的剧本');
          },
          async loadScreenplayProviders() {
            if (!this.supportsScreenplayWorkflow()) return;
            try {
              const res = await fetch(`/api/screenplay/${this.currentProject}/providers`);
              const data = await res.json();
              if (!res.ok) throw new Error(data.detail || '剧本 provider 加载失败');
              this.screenplaySession.providers = data || [];
              const defaultProvider = (data || []).find(x => x.is_default);
              if (!this.screenplaySession.provider && defaultProvider) {
                this.screenplaySession.provider = defaultProvider.name;
              }
            } catch (err) {
              this.screenplaySession.error = err.message;
            }
          },
          buildScreenplayPreviewPayload() {
            const payload = { ...this.formValues };
            payload.platform = payload.platform || 'douyin';
            payload.style = payload.style || 'tech';
            payload.topic = payload.topic || this.getProjectDisplayName(this.currentProject) || null;
            payload.video_duration = Number(payload.video_duration || payload.duration || 30);
            payload.screenplay_provider = this.screenplaySession.provider || null;
            return payload;
          },
          canGenerateScreenplay() {
            return this.supportsScreenplayWorkflow() && !!(this.formValues.platform || 'douyin');
          },
          async generateScreenplayPreview() {
            this.screenplaySession.previewLoading = true;
            this.screenplaySession.error = null;
            try {
              const res = await fetch(`/api/screenplay/${this.currentProject}/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payload: this.buildScreenplayPreviewPayload() })
              });
              const data = await res.json();
              if (!res.ok) throw new Error(data.detail || '剧本生成失败');
              this.screenplaySession.screenplay = data.screenplay;
              this.screenplaySession.providerUsed = data.provider_used;
              this.screenplaySession.fallbackUsed = !!data.fallback_used;
              this.screenplaySession.dirtySceneIds = [];
              this.screenplaySession.generatedAt = new Date().toLocaleString('zh-CN');
              this.addLog(`🧠 剧本已生成，provider: ${data.provider_used}${data.fallback_used ? ' (fallback)' : ''}`);
            } catch (err) {
              this.screenplaySession.error = err.message;
              this.addLog(`❌ 剧本生成失败: ${err.message}`);
            } finally {
              this.screenplaySession.previewLoading = false;
            }
          },
          markSceneDirty(sceneId) {
            if (!this.screenplaySession.dirtySceneIds.includes(sceneId)) {
              this.screenplaySession.dirtySceneIds.push(sceneId);
            }
          },
          async saveScreenplayEdits() {
            if (!this.screenplaySession.screenplay) return;
            this.screenplaySession.saveLoading = true;
            this.screenplaySession.error = null;
            try {
              const sceneOverrides = {};
              (this.screenplaySession.screenplay.scenes || []).forEach(scene => {
                if (this.screenplaySession.dirtySceneIds.includes(scene.id)) {
                  sceneOverrides[scene.id] = scene.narration;
                }
              });
              const payload = {
                screenplay: this.screenplaySession.screenplay,
                screenplay_provider: this.screenplaySession.provider || null,
                title: this.screenplaySession.screenplay.title,
                logline: this.screenplaySession.screenplay.logline,
                scene_narration_overrides: sceneOverrides,
              };
              const res = await fetch(`/api/screenplay/${this.currentProject}/preview`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ payload })
              });
              const data = await res.json();
              if (!res.ok) throw new Error(data.detail || '剧本改稿失败');
              this.screenplaySession.screenplay = data.screenplay;
              this.screenplaySession.providerUsed = data.provider_used;
              this.screenplaySession.fallbackUsed = !!data.fallback_used;
              this.screenplaySession.dirtySceneIds = [];
              this.addLog(`✍️ 剧本改稿已保存`);
            } catch (err) {
              this.screenplaySession.error = err.message;
              this.addLog(`❌ 剧本改稿失败: ${err.message}`);
            } finally {
              this.screenplaySession.saveLoading = false;
            }
          },

          async fetchProjects() {
            this.loadingProjects = true;
            this.error = null;
            try {
              const res = await fetch('/api/registry');
              if (!res.ok) throw new Error("API连接失败");
              const data = await res.json();
              this.projects = data.projects;
            } catch (err) {
              this.error = "无法连接到后台服务，请确认 dashboard.py 正在运行。";
              this.addLog("系统错误: " + err);
            } finally {
              this.loadingProjects = false;
            }
          },
          async fetchVizBackends() {
            try {
              const res = await fetch('/api/viz/backends');
              if (res.ok) {
                const data = await res.json();
                this.vizBackends = data.backends || [];
              }
            } catch (e) {
              // Non-critical — silently ignore
            }
          },
          toggleProject(projName) {
            this.currentProject = this.currentProject === projName ? null : projName;
          },
          async selectTask(projectName, taskName) {
            this.currentProject = projectName;
            this.currentTask = { name: taskName };
            this.loadingTask = true;
            this.taskParams = [];
            this.formValues = {};
            this.taskSuccess = false;
            this.currentJobResult = null;
            this.lastFailure = null;
            this.lastJobId = null;
            this.outcomeBannerDismissed = false;
            this.showSceneLogs = false;
            this.expandedSceneKey = null;
            this.resetScreenplaySession();
            this.logs = [];
            this.addLog(`已选中任务: ${this.getFriendlyProjectName(projectName)} - ${this.getFriendlyTaskName(taskName)}`);

            try {
              const res = await fetch(`/api/inspect/${projectName}/${taskName}`);
              let data = {};
              try {
                data = await res.json();
              } catch (e) {
                data = {};
              }
              if (!res.ok) {
                let msg = this._apiErrorMessage(data, res.statusText);
                if (res.status === 404) {
                  msg = msg && msg !== 'Not Found' ? msg : `任务元数据不存在（404）：${projectName} / ${taskName}`;
                }
                throw new Error(msg);
              }

              this.taskDetails = data;
              this.taskParams = data.parameters || [];
              this.resetForm();
              if (this.supportsScreenplayWorkflow()) {
                await this.loadScreenplayProviders();
              }

            } catch (err) {
              this.addLog(`元数据加载失败: ${err}`);
            } finally {
              this.loadingTask = false;
            }
          },
          resetForm() {
            this.formValues = {};
            this.taskParams.forEach(p => {
               const config = this.getFieldConfig(p.name);
               let def = config.default !== undefined ? config.default : p.default;

               if (p.type === 'bool' || config.type === 'bool') {
                  this.formValues[p.name] = (def === true || def === 'True');
               } else {
                  if (def !== null && def !== undefined) {
                      this.formValues[p.name] = def;
                  }
               }
            });
          },
          async runTask() {
            if (!this.currentProject || !this.currentTask) return;
            if (this.agentRunning && this.agentCompiledResult && this.agentCompiledResult.project === this.currentProject) {
              this.addLog('⚠️ 意图会话正在对该项目渲染，请等待完成后再试');
              return;
            }
            this.running = true;
            this.taskSuccess = false;
            this.currentJobResult = null;
            this.lastFailure = null;
            this.outcomeBannerDismissed = false;
            this.showSceneLogs = false;
            this.expandedSceneKey = null;
            this.addLog(`>>> 开始执行任务...`);

            const payload = {};
            for (const [key, val] of Object.entries(this.formValues)) {
                if (val !== "" && val !== null && val !== undefined && !this.isHiddenField(key)) {
                    payload[key] = val;
                }
            }
            if (this.canAttachScreenplay() && this.screenplaySession.screenplay) {
              payload.screenplay = this.screenplaySession.screenplay;
              const sc = this.screenplaySession.screenplay;
              const n = (sc.scenes && sc.scenes.length) || 0;
              this.addLog(`📜 本次运行将向后端传递剧本 JSON（${sc.title || 'untitled'}，${n} scenes）`);
            } else if (this.canAttachScreenplay() && this.allowRunWithoutScreenplay) {
              this.addLog(`⚠️ 本次未附带剧本：后端将按各项目默认逻辑（表单参数/内部默认叙事）出片，不以 Screenplay 驱动节拍。`);
            }

            try {
              const res = await fetch(`/api/run/${this.currentProject}/${this.currentTask.name}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ kwargs: payload })
              });

              const data = await res.json();
              if (!res.ok) throw new Error(data.detail || res.statusText);

              this.lastJobId = data.job_id || null;
              this.addLog(`✅ 指令发送成功: ${data.message}`);
              this.addLog(`⏳ 等待后台执行结果 (Job ID: ${data.job_id})...`);
              this.pollJob(data.job_id);

            } catch (err) {
              this.addLog(`❌ 启动失败: ${err}`);
              this.running = false;
            }
          },
          async pollJob(jobId) {
             const sleep = ms => new Promise(r => setTimeout(r, ms));
             const maxRetries = 300;
             let attempts = 0;

             while (attempts < maxRetries) {
                await sleep(2000);
                attempts++;

                try {
                    const res = await fetch(`/api/jobs/${jobId}`);
                    if (!res.ok) {
                         this.addLog(`⚠️ 查询任务状态失败: ${res.statusText}`);
                         continue;
                    }
                    const job = await res.json();

                    if (job.status === 'success') {
                        this.addLog(`🎉 任务执行成功!`);
                        this.lastFailure = null;
                        if (job.result) {
                            this.currentJobResult = job.result;
                            this.expandedSceneKey = null;
                            if (typeof job.result === 'object') {
                                if (job.result.final_video_path) this.addLog(`🎥 视频输出: ${job.result.final_video_path}`);
                                if (job.result.rendered_video_path) this.addLog(`🎞️ 渲染文件: ${job.result.rendered_video_path}`);
                                if (job.result.scene_schedule) {
                                    const sceneCount = (job.result.scene_schedule.scenes || []).length;
                                    this.addLog(`🧭 已加载 scene schedule，共 ${sceneCount} 个 scenes`);
                                    if (job.result.scene_schedule_path) {
                                        this.addLog(`📝 Scene schedule metadata: ${job.result.scene_schedule_path}`);
                                    }
                                }
                            } else {
                                this.addLog(`返回结果: ${job.result}`);
                            }
                        }
                        // Log self-correction summary if retries happened
                        if (job.result && job.result.self_correction) {
                          const sc = job.result.self_correction;
                          this.addLog(`🔄 自动修复: 经过 ${sc.total_attempts || 0} 次重试后成功`);
                        }
                        this.taskSuccess = true;
                        this.addLog('✅ 请在下方「任务结果验收」核对产出路径；有节拍表时可继续查看 Scene Schedule。');
                        this.running = false;
                        return;
                    } else if (job.status === 'failed') {
                        const errMsg = job.error || '未知错误';
                        this.addLog(`❌ 任务执行失败: ${errMsg}`);
                        if (job.log && job.log.length > 0) {
                           job.log.slice(-3).forEach(l => this.addLog(`[JobLog] ${l}`));
                        }
                        // Extract self-correction info from job result (lifecycle stores it on failure)
                        const scInfo = (job.result && job.result.self_correction) || null;
                        this.lastFailure = {
                          error: errMsg,
                          jobLog: job.log || [],
                          jobId: jobId,
                          selfCorrection: scInfo,
                        };
                        if (scInfo) {
                          this.addLog(`🔍 错误分类: ${scInfo.error_category || '未知'}${scInfo.auto_correctable ? '（已尝试自动修复）' : ''}`);
                          if (scInfo.suggested_fix) this.addLog(`💡 建议: ${scInfo.suggested_fix}`);
                        }
                        this.taskSuccess = false;
                        this.currentJobResult = null;
                        this.addLog('❌ 请在下方「任务结果验收」查看详情，可「使用当前参数重试」。');
                        this.running = false;
                        return;
                    } else {
                        if (attempts % 5 === 0) {
                            this.addLog(`⏳ 任务正在执行中... (${attempts * 2}s)`);
                        }
                    }
                } catch (e) {
                    console.error(e);
                }
             }

             this.addLog(`⏱️ 任务轮询超时，请检查后台日志。`);
             this.lastFailure = {
               error: '轮询超时：任务可能仍在后台执行，请查看终端日志。',
               jobLog: [],
               jobId: jobId,
             };
             this.taskSuccess = false;
             this.running = false;
          },

          async createProject() {
            this.creatingProject = true;
            this.createError = null;

            try {
               const res = await fetch('/api/projects', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(this.newProject)
               });

               const data = await res.json();
               if (!res.ok) throw new Error(data.detail || '创建失败');

               const resolved = data.name || this.newProject.name;
               this.addLog(`✨ 新项目创建成功，目录名：${resolved}` + (resolved !== this.newProject.name ? `（已规范化，输入为 ${this.newProject.name}）` : ''));
               this.newProject = { name: '', description: '' };
               if (this.bsModal) this.bsModal.hide();
               await this.fetchProjects();
               // Auto-navigate to the core render task so user lands in creation mode
               await this.selectTask(resolved, 'render');
               this.addLog('📌 已自动进入「核心渲染」任务。请先配置基础参数，然后在下方「脚本交付」定义你的视频内容。');

            } catch (err) {
               this.createError = err.message;
            } finally {
               this.creatingProject = false;
            }
          },

          getProjectTaskGroups(tasks) {
             const groups = { prep: [], core: [] };

             tasks.forEach(task => {
                if (HIDDEN_TASKS.has(task.name)) return;
                if (task.name === 'smoke_check' || task.name === 'scene_schedule_preview') {
                    groups.prep.push(task);
                } else {
                    groups.core.push(task);
                }
             });
             return groups;
           },

           async fetchSettings() {
             this.settingsLoading = true;
             try {
                const res = await fetch('/api/settings');
                if (!res.ok) throw new Error("加载配置失败");
                const data = await res.json();
                // Initialize UI-only state
                data.validating = false;
                data.validationSuccess = false;
                data.validationError = false;
                data.validationMessage = '';
                data.available_models = [];
                data._showApiKey = false;
                data._showPexelsKey = false;
                data._durationError = false;
                data._saveSuccess   = false;
                data._saveError     = false;
                data._saveMessage   = '';
                // 保底默认值（后端未返回或为 0 时补充）
                if (!data.video_width)  data.video_width  = 1080;
                if (!data.video_height) data.video_height = 1920;
                // 若 width×height 不在预设列表中，则重置为默认值，避免下拉显示空
                const VALID_RESOLUTIONS = new Set([
                  '1920x1080','1280x720','1080x1920','1080x1350',
                  '3840x2160','2560x1440','720x1280'
                ]);
                if (!VALID_RESOLUTIONS.has(`${data.video_width}x${data.video_height}`)) {
                  data.video_width  = 1080;
                  data.video_height = 1920;
                }
                this.settings = data;
             } catch (err) {
                this.addLog(`❌ 获取全局配置失败: ${err.message}`);
             } finally {
                this.settingsLoading = false;
             }
           },

           /** 眼睛按钮：展开 API Key 明文（若当前为掩码则先拉真实值）*/
           async toggleShowApiKey() {
              if (!this.settings._showApiKey && this.settings.openai_api_key && this.settings.openai_api_key.includes('...')) {
                 try {
                    const res = await fetch('/api/settings/reveal-keys');
                    const data = await res.json();
                    if (data.openai_api_key) this.settings.openai_api_key = data.openai_api_key;
                 } catch (_) {}
              }
              this.settings._showApiKey = !this.settings._showApiKey;
           },

           /** 眼睛按钮：展开 Pexels Key 明文（若当前为掩码则先拉真实值）*/
           async toggleShowPexelsKey() {
              if (!this.settings._showPexelsKey && this.settings.pexels_api_key && this.settings.pexels_api_key.includes('...')) {
                 try {
                    const res = await fetch('/api/settings/reveal-keys');
                    const data = await res.json();
                    if (data.pexels_api_key) this.settings.pexels_api_key = data.pexels_api_key;
                 } catch (_) {}
              }
              this.settings._showPexelsKey = !this.settings._showPexelsKey;
           },

           /** 分辨率下拉：同步设置 video_width 和 video_height */
           applyResolution(val) {
              const parts = val.split('x').map(Number);
              if (parts.length === 2 && parts[0] > 0 && parts[1] > 0) {
                 this.settings.video_width = parts[0];
                 this.settings.video_height = parts[1];
              }
           },

           /** 可选次操作：拉取模型列表填充 datalist，不影响保存主流程 */
           async validateOpenAI() {
              if (!this.settings.openai_base_url) return;
              this.settings.validating = true;
              this.settings.validationSuccess = false;
              this.settings.validationError = false;
              this.settings.validationMessage = '';
              try {
                  // 若 key 是脱敏值（含 ...），先拉取真实 key 再发请求
                  let apiKey = this.settings.openai_api_key || '';
                  if (apiKey.includes('...')) {
                     try {
                        const rr = await fetch('/api/settings/reveal-keys');
                        const rd = await rr.json();
                        if (rd.openai_api_key) {
                           apiKey = rd.openai_api_key;
                           this.settings.openai_api_key = apiKey;
                        }
                     } catch (_) {}
                  }
                  const res = await fetch('/api/settings/validate-openai', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                          api_key: apiKey,
                          base_url: this.settings.openai_base_url,
                          model_hint: this.settings.openai_model || ''
                      })
                  });
                  const data = await res.json();
                  if (data.valid) {
                      this.settings.validationSuccess = true;
                      this.settings.available_models = data.models || [];
                      // 若当前填的 model 不在列表中，自动补填第一个建议值
                      if (this.settings.available_models.length > 0 && !this.settings.available_models.includes(this.settings.openai_model)) {
                          this.settings.openai_model = this.settings.available_models[0];
                      }
                  } else {
                      this.settings.validationError = true;
                      this.settings.validationMessage = data.error || '连接失败';
                  }
              } catch (err) {
                  this.settings.validationError = true;
                  this.settings.validationMessage = err.message;
              } finally {
                  this.settings.validating = false;
              }
           },

           async saveSettings() {
              // 前端校验：数字范围 / 必填项
              const dur = this.settings.video_total_duration;
              if (!(dur >= 1 && dur <= 7200)) {
                 this.settings._durationError = true;
                 return;
              }
              const form = document.getElementById('settingsForm');
              if (!form.checkValidity()) {
                 form.classList.add('was-validated');
                 return;
              }
              form.classList.remove('was-validated');
              // 清除上次提示
              this.settings._saveSuccess = false;
              this.settings._saveError   = false;
              this.settings._saveMessage = '';
              this.settingsLoading = true;
              try {
                 const res = await fetch('/api/settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.settings)
                 });
                 const data = await res.json().catch(() => ({}));
                 if (!res.ok) {
                    // 后端明确返回错误
                    const msg = data.detail || data.message || `HTTP ${res.status}`;
                    throw new Error(msg);
                 }
                 // 成功：显示内联提示，2 秒后关闭弹窗
                 this.settings._saveSuccess = true;
                 this.settings._saveMessage = '配置已成功保存至 .env';
                 this.addLog("✅ 全局配置已更新并保存至 .env");
                 setTimeout(() => {
                    if (this.bsSettingsModal) this.bsSettingsModal.hide();
                    this.settings._saveSuccess = false;
                 }, 1500);
              } catch (err) {
                 this.settings._saveError   = true;
                 this.settings._saveMessage = `保存失败：${err.message}`;
                 this.addLog(`❌ 保存配置失败: ${err.message}`);
              } finally {
                 this.settingsLoading = false;
              }
           },

          // ── AI Agent Panel Methods ──
          openSettingsModal() {
            if (this.bsSettingsModal) {
              this.fetchSettings();
              this.bsSettingsModal.show();
            }
          },

          /** 从当前会话历史里取最后一条 compiled_template（用作 previous 上下文） */
          lastCompiledTemplate() {
            const turns = this.studioSessionDetail?.turns;
            if (!Array.isArray(turns)) return null;
            for (let i = turns.length - 1; i >= 0; i--) {
              if (turns[i].role !== 'user' && turns[i].compiled_template) {
                return turns[i].compiled_template;
              }
            }
            return null;
          },

          /** 一键加载会话最后一次编译结果到主区，供继续迭代 */
          loadLastCompiledTemplate() {
            const tpl = this.lastCompiledTemplate();
            if (!tpl) return;
            this.agentCompiledResult = tpl;
            // 对于已保存的模板，直接使用其中的 kwargs（没有task_parameters）
            this.agentEditedKwargs = { ...(tpl.kwargs || {}) };
            this.agentCompileError = null;
            this.agentLogs = ['📋 已载入上次编译结果，可直接运行或修改提示后重新编译'];
          },

          async compileAgentPrompt() {
            if (!this.agentPrompt.trim()) return;
            this.agentCompiling = true;
            this.agentCompileError = null;
            this.agentCompiledResult = null;
            this.agentEditedKwargs = {};
            this.agentJobSuccess = false;
            this.agentJobFailure = null;
            this.agentJobResult = null;
            this.agentLogs = [];
            // 若侧栏有选中会话，携带 session_id 和 previous 做多轮对话
            const sessionId = this.selectedStudioSessionId || null;
            const previous = sessionId ? this.lastCompiledTemplate() : null;
            if (sessionId) this.agentLogs.push(`🗂 会话 ${sessionId.slice(0, 8)}… 已关联`);
            try {
              const body = { prompt: this.agentPrompt.trim() };
              if (sessionId) { body.session_id = sessionId; body.persist_turns = true; }
              if (previous) { body.previous = previous; }
              const res = await fetch('/api/agent/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
              });
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              if (!data.success) {
                throw new Error((data.errors || []).join('；') || '编译失败（未知原因）');
              }
              this.agentCompiledResult = data.standard_request;
              
              // 合并 task_parameters 与 kwargs：确保所有参数都显示，包括默认值
              this.agentEditedKwargs = {};
              if (data.task_parameters && Array.isArray(data.task_parameters)) {
                // 先从参数定义加载默认值
                data.task_parameters.forEach(param => {
                  if (param.name && 'default' in param) {
                    this.agentEditedKwargs[param.name] = param.default;
                  }
                });
                // 再用编译的kwargs覆盖（这样保留AI生成的值）
                if (data.standard_request.kwargs) {
                  Object.assign(this.agentEditedKwargs, data.standard_request.kwargs);
                }
              } else {
                // 如果没有task_parameters，就直接用编译的kwargs
                this.agentEditedKwargs = { ...(data.standard_request.kwargs || {}) };
              }
              
              this.agentLogs.push(`✅ 编译成功 → 项目：${data.standard_request.project}，任务：${data.standard_request.task}`);
              if (data.standard_request.intent_summary) {
                this.agentLogs.push(`💡 AI 理解：${data.standard_request.intent_summary}`);
              }
              // 显示参数信息
              if (data.task_parameters && Array.isArray(data.task_parameters) && data.task_parameters.length > 0) {
                this.agentLogs.push(`📋 任务参数：${data.task_parameters.map(p => p.name).join(', ')}`);
              }
              (data.warnings || []).forEach(w => this.agentLogs.push(`⚠️ ${w}`));
              // 编译成功后刷新侧栏会话详情；若用户已切换会话则不强制重选
              if (sessionId && this.selectedStudioSessionId === sessionId) {
                await this.selectStudioSession(sessionId);
              }
            } catch (err) {
              this.agentCompileError = err.message;
              this.agentLogs.push(`❌ 编译失败：${err.message}`);
            } finally {
              this.agentCompiling = false;
            }
          },

          async runAgentJob() {
            if (!this.agentCompiledResult) return;
            if (this.running && this.currentProject === this.agentCompiledResult.project) {
              this.agentLogs.push('⚠️ 项目与任务面板正在渲染同一项目，请等待完成后再试');
              return;
            }
            
            this.agentRunning = true;
            this.agentJobSuccess = false;
            this.agentJobFailure = null;
            this.agentJobResult = null;
            this.agentJobId = null;
            this.agentLinkedSessionId = this.selectedStudioSessionId;
            
            // session_id 通过 query 参数传递，不放进 StandardVideoJobRequest 请求体（extra=forbid）
            const payload = { 
              ...this.agentCompiledResult, 
              kwargs: { ...this.agentEditedKwargs },
            };
            const runUrl = this.agentLinkedSessionId
              ? `/api/agent/run?session_id=${encodeURIComponent(this.agentLinkedSessionId)}`
              : '/api/agent/run';
            try {
              const res = await fetch(runUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
              });
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              this.agentJobId = data.job_id;
              this.agentLogs.push(`▶ 任务已提交  Job ID: ${data.job_id}`);
              this.agentPollJob(data.job_id);
            } catch (err) {
              this.agentLogs.push(`❌ 运行失败：${err.message}`);
              this.agentRunning = false;
            }
          },

          async agentPollJob(jobId) {
            const sleep = ms => new Promise(r => setTimeout(r, ms));
            let attempts = 0;
            while (attempts < 300) {
              await sleep(2000);
              attempts++;
              try {
                const res = await fetch(`/api/jobs/${jobId}`);
                if (!res.ok) continue;
                const job = await res.json();
                if (job.status === 'success') {
                  this.agentJobSuccess = true;
                  this.agentJobResult = job.result || {};
                  
                  // 渲染完成后，自动生成会话标题并标记为已完成
                  if (this.agentLinkedSessionId) {
                    const autoTitle = this.generateSessionTitleFromPrompt(this.agentPrompt);
                    if (autoTitle) {
                      await this.updateSessionTitle(this.agentLinkedSessionId, autoTitle);
                    }
                    // 标记会话为已完成并刷新列表
                    try {
                      await fetch(`/api/v1/sessions/${encodeURIComponent(this.agentLinkedSessionId)}/complete`, {
                        method: 'POST'
                      });
                      await this.fetchStudioSessions();  // 刷新列表以更新 is_completed 状态
                      // 若用户当前仍在此会话，同步刷新 turns
                      if (this.selectedStudioSessionId === this.agentLinkedSessionId) {
                        await this.refreshStudioSessionDetail();
                      }
                    } catch (e) {
                      console.error('Failed to mark session as completed:', e);
                    }
                  }
                  
                  if (job.result && job.result.final_video_path) {
                    this.agentLogs.push(`🎥 视频输出：${job.result.final_video_path}`);
                  } else if (job.result && job.result.rendered_video_path) {
                    this.agentLogs.push(`🎞️ 渲染文件：${job.result.rendered_video_path}`);
                  }
                  this.agentLogs.push('🎉 渲染成功！');
                  this.agentRunning = false;
                  return;
                } else if (job.status === 'failed') {
                  this.agentJobFailure = { error: job.error || '未知错误', jobId };
                  this.agentLogs.push(`❌ 渲染失败：${job.error || '未知错误'}`);
                  this.agentRunning = false;
                  return;
                } else if (attempts % 5 === 0) {
                  this.agentLogs.push(`⏳ 渲染中… (${attempts * 2}s)`);
                }
              } catch (e) { console.error(e); }
            }
            this.agentLogs.push('⏱️ 轮询超时，请查看终端日志');
            this.agentRunning = false;
          },

          generateSessionTitleFromPrompt(prompt) {
            // 从提示文本生成简洁的会话标题（取前 50 个字符或第一句）
            if (!prompt || !prompt.trim()) return null;
            const text = prompt.trim();
            // 只取中文、字母、数字
            const cleaned = text.replace(/[^\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ffa-zA-Z0-9（）()，。]/g, ' ').trim();
            if (!cleaned) return null;
            // 取前 40 个字符
            return cleaned.substring(0, 40);
          },

          resetAgentPanel() {
            this.agentPrompt = '';
            this.agentCompiling = false;
            this.agentCompileError = null;
            this.agentCompiledResult = null;
            this.agentEditedKwargs = {};
            this.agentRunning = false;
            this.agentJobId = null;
            this.agentJobSuccess = false;
            this.agentJobFailure = null;
            this.agentJobResult = null;
            this.agentLogs = [];
          },

          // ── Code Studio Methods ──

          csProjectChanged() {
            this.csSelectedTaskName = '';
            this.csSessions = [];
            this.csSelectedSessionId = null;
            this.csSessionDetail = null;
            this.csLatestPatch = null;
            this.csCompileError = null;
            this.csApplyError = null;
            this.csApplySuccess = null;
            // 项目只有一个任务时自动预选
            if (this.csTasksForSelectedProject.length === 1) {
              this.csSelectedTaskName = this.csTasksForSelectedProject[0].name;
            }
            if (this.csSelectedProjectName) this.csFetchSessions();
          },

          csTaskChanged() {
            this.csSessions = [];
            this.csSelectedSessionId = null;
            this.csSessionDetail = null;
            this.csLatestPatch = null;
            this.csCompileError = null;
            this.csApplyError = null;
            this.csApplySuccess = null;
            if (this.csSelectedProjectName) this.csFetchSessions();
          },

          async csFetchSessions() {
            if (!this.csSelectedProjectName) return;
            this.csSessionsLoading = true;
            this.csSessionsError = null;
            try {
              let url = `/api/code-studio/sessions?project_name=${encodeURIComponent(this.csSelectedProjectName)}&limit=30`;
              if (this.csSelectedTaskName) {
                url += `&task_name=${encodeURIComponent(this.csSelectedTaskName)}`;
              }
              const res = await fetch(url);
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              this.csSessions = data.items || [];
            } catch (err) {
              this.csSessionsError = `加载会话失败：${err.message}`;
            } finally {
              this.csSessionsLoading = false;
            }
          },

          async csCreateSession() {
            if (!this.csSelectedProjectName) return;
            try {
              const res = await fetch('/api/code-studio/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  project_name: this.csSelectedProjectName,
                  task_name: this.csSelectedTaskName || null,
                  title: null,  // 服务端自动生成序号标题
                }),
              });
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              await this.csFetchSessions();
              this.csSelectSession(data.session_id);
            } catch (err) {
              this.csSessionsError = `新建会话失败：${err.message}`;
            }
          },

          async csSelectSession(sessionId) {
            this.csSelectedSessionId = sessionId;
            this.csLatestPatch = null;
            this.csCompileError = null;
            this.csApplyError = null;
            this.csApplySuccess = null;
            this.csSessionDetailLoading = true;
            try {
              const res = await fetch(`/api/code-studio/sessions/${sessionId}`);
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              this.csSessionDetail = data;
              // 恢复最近补丁（最后一条 assistant 轮次）
              const assistantTurns = (data.turns || []).filter(t => t.role === 'assistant');
              if (assistantTurns.length > 0) {
                const last = assistantTurns[assistantTurns.length - 1];
                this.csLatestPatch = {
                  file_path: last.file_path,
                  new_content: last.code_patch,
                  explanation: last.content_text,
                  turn_id: last.id,
                };
                this.csLatestPatchApplied = !!last.applied_at;
              }
            } catch (err) {
              this.csSessionsError = `加载会话详情失败：${err.message}`;
            } finally {
              this.csSessionDetailLoading = false;
            }
          },

          csClearSession() {
            this.csSelectedSessionId = null;
            this.csSessionDetail = null;
            this.csLatestPatch = null;
            this.csCompileError = null;
            this.csApplyError = null;
            this.csApplySuccess = null;
          },

          async csCompile() {
            if (!this.csPrompt.trim() || !this.csSelectedSessionId) return;
            this.csCompiling = true;
            this.csCompileError = null;
            this.csLatestPatch = null;
            this.csLatestPatchApplied = false;
            this.csApplyError = null;
            this.csApplySuccess = null;
            try {
              const body = { prompt: this.csPrompt.trim() };
              if (this.csFileHint.trim()) body.file_hint = this.csFileHint.trim();
              const res = await fetch(`/api/code-studio/sessions/${this.csSelectedSessionId}/compile`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
              });
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              if (!data.success) {
                this.csCompileError = (data.errors || ['编译失败']).join('; ');
                return;
              }
              // 刷新会话详情获取最新轮次 id
              await this.csSelectSession(this.csSelectedSessionId);
            } catch (err) {
              this.csCompileError = `编译请求失败：${err.message}`;
            } finally {
              this.csCompiling = false;
            }
          },

          async csApply() {
            if (!this.csLatestPatch || !this.csSelectedSessionId) return;
            this.csApplying = true;
            this.csApplyError = null;
            this.csApplySuccess = null;
            try {
              const res = await fetch(`/api/code-studio/sessions/${this.csSelectedSessionId}/apply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ turn_id: this.csLatestPatch.turn_id, confirm: true }),
              });
              const data = await res.json();
              if (!res.ok) throw new Error(this._apiErrorMessage(data, res.statusText));
              if (data.success) {
                this.csLatestPatchApplied = true;
                this.csApplySuccess = `✅ 已写入：${data.written_path}`;
                // 刷新侧栏历史（applied_at 时间戳更新）
                await this.csSelectSession(this.csSelectedSessionId);
              } else {
                this.csApplyError = data.error || '写入失败';
              }
            } catch (err) {
              this.csApplyError = `写入请求失败：${err.message}`;
            } finally {
              this.csApplying = false;
            }
          },

          csCopyPatch() {
            if (!this.csLatestPatch) return;
            try {
              navigator.clipboard.writeText(this.csLatestPatch.new_content);
            } catch (e) { /* ignore */ }
          },

         }
      }).mount('#app');
