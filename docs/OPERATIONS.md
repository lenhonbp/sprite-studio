# Vận hành và giữ quyền kiểm soát

Bản này chạy trên Cloudflare Workers thông qua Sites. R2 binding `BUCKET` lưu file project theo Site-scoped user ID. Conditional ETag writes bảo vệ thao tác đồng thời; toàn bộ nhóm lệnh được kiểm tra trước khi lưu. Không có migration D1 hay khởi tạo bảng trong request.

Identity `oai-authenticated-user-id` phải do lớp Sites đã xác thực đưa vào. API yêu cầu identity; không dùng service bypass token để giả làm một người dùng. Project được tách riêng theo account identity. Thư viện thiết bị là dữ liệu local, không phải hồ sơ cloud dùng chung.

`/health` báo phiên bản và có binding storage hay không. Nó không xác nhận project cá nhân, OAuth/plugin hoặc chất lượng hình ảnh. `/mcp` có server/discover, initialize, tools/list, tools/call, resources/list/read; widget dùng `text/html;profile=mcp-app`.

Khi chuyển hosting, cần adapter xác thực đáng tin cậy, ổ lưu trữ hỗ trợ atomic compare-and-swap, cùng lớp phân quyền tương đương. Không tin identity header do khách Internet tự gửi. `.openai/hosting.json` hiện nhận diện Site của chủ sở hữu; dùng lại để cập nhật Site đó, không dùng nó để tạo Site thuộc người khác.

Backup nên lưu: project JSON nguồn, backup thư viện thiết bị, toàn bộ ZIP mã nguồn và các gói PNG/GIF/sheet đã xuất. Undo online là lịch sử giới hạn, không phải backup lâu dài. Bản dựng offline không cần hosting sau khi tải xuống; dữ liệu browser vẫn cần xuất file để chuyển máy.

ZIP chứa mã nguồn và công cụ, không chứa project cloud cá nhân đang chỉnh, token đăng nhập, Git credentials hoặc native canvas binaries. Muốn chuyển project đang dùng trên web, bấm Lưu JSON ngay trong editor.

## Git/local v3.3

For the shared local editor + agent CLI + stdio MCP workflow, use docs/LOCAL.md. This mode does not require the cloud plugin or authenticated hosting headers. All processes must use the same absolute data directory.
