from pydantic import BaseModel, Field
from tool import Tool


class SkillManagerInput(BaseModel):
    """技能管理输入参数"""
    skill_name: str = Field(
        ...,
        description="要获取的技能名称，可选：天气助手、ReAct 推理行动、CoC 7th Edition Character Data Architect、技能自动加载器"
    )


class SkillManagerTool(Tool):
    """技能管理工具 - 获取指定技能的完整内容"""

    name = "skill_manager"
    desc = "根据技能名称获取该技能的完整能力和工作流程信息，用于在使用某个技能前先加载了解该技能"
    input_schema = SkillManagerInput

    # 内置技能信息库
    SKILLS_DB = {
        "天气助手": {
            "name": "天气助手",
            "desc": "帮助用户获取实时天气",
            "content": """
工作流程
- 如果用户没有说明时间，那么调用工具查询当前时间
- 根据上一步的时间，调用工具查询用户指定地点的天气
- 尽可能简短的告知用户天气信息，例如：东京：18° 晴
"""
        },
        "ReAct 推理行动": {
            "name": "ReAct 推理行动",
            "desc": "遵循 ReAct 范式进行思考和行动",
            "content": """
## ReAct 范式 (Reasoning + Acting)

你的发言遵循 ReAct 范式，循环执行以下步骤：

### 1. 思考 (Thought)
分析用户问题，判断是否需要调用工具
- 理解用户意图
- 评估当前掌握的信息是否足够
- 决定下一步：直接回答 或 调用工具获取更多信息

### 2. 行动 (Action)
若需要调用工具，按格式输出工具名和参数
- 明确指定工具名称
- 提供完整的参数
- 一次只执行一个行动

### 3. 观察 (Observation)
等待工具返回结果后，结合结果继续思考
- 分析工具返回的数据
- 判断信息是否满足需求
- 决定是否需要进一步行动

### 4. 汇报 (Report)
向用户汇报结果（汇报可以插入到任何一个步骤之前或之后）
- 总结当前进展
- 说明正在进行的操作
- 呈现最终结果

---

## 格式要求

- 使用 `<思考></思考>` 标签包裹思考内容
- 使用 `<汇报></汇报>` 标签包裹汇报内容
- 行动和观察不需要特殊标记
"""
        },
        "CoC 7th Edition Character Data Architect": {
            "name": "CoC 7th Edition Character Data Architect",
            "desc": "严格按照《克苏鲁的呼唤》第七版规则，利用掷骰工具生成准确的角色基础属性与派生属性",
            "content": """
根据《守秘人规则书》第七版规则和 MCP 掷骰工具，系统化地完成属性生成、派生数值计算以及年龄调整。

#### **Workflow Logic (Workflow):**

1.  **第一阶段：核心属性掷骰**
    AI 必须调用 `roll_dice` 工具执行以下掷骰表达式，并记录结果：
    *   **力量 (STR)、体质 (CON)、敏捷 (DEX)、外貌 (APP)、意志 (POW)**：分别调用 `roll_dice(expression="3d6")`。
    *   **体型 (SIZ)、智力 (INT)、教育 (EDU)**：分别调用 `roll_dice(expression="2d6+6")`。
    *   **幸运 (Luck)**：调用 `roll_dice(expression="3d6")`。
    *   **计算原始值**：将以上结果均**乘以 5**，得出 15-90 之间的全额属性值。

2.  **第二阶段：年龄调整逻辑（默认 20-39 岁）**
    除非玩家另有要求，否则按标准成年人（20-39岁）处理：
    *   **教育增强检定**：调用 `roll_dice(expression="1d100")`。若结果 > 当前教育值，则调用 `roll_dice(expression="1d10")` 并加到教育属性上（上限 99）。

3.  **第三阶段：计算派生属性 (Derived Stats)**
    基于阶段一、二确定的属性全额值进行数学计算：
    *   **理智值 (SAN)**：初始值 = 意志全额值。
    *   **魔法值 (MP)**：初始值 = 意志全额值的 1/5（向下取整）。
    *   **生命值 (HP)**：(体质 + 体型) / 10（向下取整）。
    *   **移动速度 (MOV)**：
        *   若 (敏捷 < 体型) 且 (力量 < 体型)：MOV 7。
        *   若 (敏捷 ≥ 体型) 或 (力量 ≥ 体型)：MOV 8。
        *   若 (力量 > 体型) 且 (敏捷 > 体型)：MOV 9。
        *   *注：若年龄 ≥ 40 岁，需根据规则进一步减除 MOV*。
    *   **体格 (Build) 与 伤害加值 (DB)**：
        计算 (力量 + 体型) 的总和：
        *   2–64：Build -2, DB -2
        *   65–84：Build -1, DB -1
        *   85–124：Build 0, DB 0
        *   125–164：Build 1, DB +1D4
        *   165–204：Build 2, DB +1D6

4.  **第四阶段：计算成功等级**
    为 8 项核心属性计算**半值 (1/2)** 和 **五分之一值 (1/5)**（向下取整），用于困难和极难检定。

#### **Format of Response (Output):**

请严格按照以下格式返回结果：

**【调查员基础属性】**
*   力量：[全额]/[半值]/[五分之值]
*   体质：[全额]/[半值]/[五分之值]
*   ...（以此类推）
*   教育：[最终增强后的全额值]
*   幸运：[全额值]

**【调查员派生数值】**
*   HP：[数值] | MP：[数值] | SAN：[数值]
*   MOV：[数值] | Build：[数值] | DB：[数值]

---

### **AI 内部指令提示词 (Prompts for Internal Logic):**

*   **原则：** 永远不要手动"发明"掷骰结果。必须等待 `roll_dice` 工具的返回结果。
*   **计算精准：** 严格执行向下取整。
*   **年龄判定：** 默认设置为 20-39 岁，如果管理员指令中包含年龄，请参照《守秘人规则书》第 31 页的年龄调整表执行属性减损（如 40-49 岁需在力量、体质或敏捷合计减去 5 点）。

**Analogy（类比）：**
作为"角色卡建筑师"，你就像一个**精密的天平**。`roll_dice` MCP 工具为你提供原材料（原始骰点），你则负责按照规则书的图纸（公式）进行加工和校准，最后交付给玩家一个符合规则逻辑的、坚固的调查员骨架。
"""
        },
        "技能自动加载器": {
            "name": "技能自动加载器",
            "desc": "在收到用户请求时自动识别并加载相关技能",
            "content": """
## 技能自动加载流程

每当收到用户请求时，必须遵循以下步骤：

### 步骤 1：分析用户请求
仔细阅读用户的问题或需求，识别其中的关键意图和主题。

### 步骤 2：检查可用技能
查看当前 Agent 已加载的所有技能列表，判断是否有与用户需求相关的技能。

当前可用技能包括：
- 天气助手：帮助用户获取实时天气
- ReAct 推理行动：遵循 ReAct 范式进行思考和行动
- CoC 7th Edition Character Data Architect：克苏鲁的呼唤7版角色卡生成
- 技能自动加载器：本技能自身

### 步骤 3：加载相关技能（关键步骤）
如果发现与用户请求相关的技能，**必须立即调用 skill_manager 工具加载该技能**。

调用方式：
```
skill_manager(skill_name="技能名称")
```

加载原则：
- 用户询问天气、时间相关 → 加载「天气助手」
- 用户提及角色卡、调查员、CoC、克苏鲁的呼唤 → 加载「CoC 7th Edition Character Data Architect」
- 用户要求复杂推理、多步骤任务 → 加载「ReAct 推理行动」
- 不确定时，可以加载多个可能相关的技能

### 步骤 4：执行任务
在确认相关技能已加载后，根据加载的技能能力和用户请求，继续思考和解决问题。

---

## 重要原则

1. **先加载，后执行**：严禁在未加载相关技能的情况下直接回答需要专业技能的问题
2. **主动识别**：即使用户没有明确提及技能名称，也要根据内容识别需要加载的技能
3. **级联加载**：某些任务可能需要多个技能配合完成，此时应依次加载所有相关技能
"""
        },
    }

    async def run(self, skill_name: str) -> dict:
        """
        根据技能名称返回该技能的完整内容

        Args:
            skill_name: 技能名称

        Returns:
            技能的完整信息（name, desc, content）
        """
        # 查找技能
        skill_info = self.SKILLS_DB.get(skill_name)

        if skill_info is None:
            available_skills = list(self.SKILLS_DB.keys())
            return {
                "success": False,
                "error": f"未找到名为 '{skill_name}' 的技能",
                "available_skills": available_skills
            }

        return {
            "success": True,
            "skill": skill_info
        }
