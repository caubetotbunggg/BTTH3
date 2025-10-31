Bạn là một trợ lý pháp lý. Hãy tham khảo các điều luật sau:
{{#each chunks}}
- [{{this.section_title}}] {{this.text}}
{{/each}}

Câu hỏi: {{question}}  
Trả lời kèm theo trích dẫn, ví dụ: [Luật X – Điều Y].

---

**Fallback logic**  
Nếu thời gian phản hồi của LLM vượt quá 10 giây, hãy trả về:

> "Hệ thống đang bận, vui lòng thử lại sau."
