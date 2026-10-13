# Git / local edition v4.1.1

Made by Nhon Le. Editor, agent CLI và MCP cùng dùng một project trên máy chạy Node. Không cần hosting hoặc API key cho chế độ này; cần Node.js 22+. Không phải agent tự chạy nền khi cuộc chat đã kết thúc.

## Khởi chạy

Giải nén hoặc clone repository, mở terminal ở thư mục có package.json:

```sh
npm start
```

Mở http://127.0.0.1:8787. Chỉnh tay trên editor, hoặc để agent chạy:

```sh
npm run studio -- read
npm run studio -- check
```

Không cần npm install để chạy editor, đồng bộ JSON, CLI authoring hoặc MCP local. Chỉ cần npm install khi render bằng CLI với native canvas. Nếu port bận: `npm start -- --port 8790`. Server chỉ lắng nghe 127.0.0.1; không sửa thành 0.0.0.0 để dùng như dịch vụ công khai.

Nếu agent chạy trên máy/cloud khác, localhost thuộc máy/cloud đó. Bạn chỉ xem được qua tính năng mở/forward port được môi trường cung cấp hoặc chạy repo trên máy của bạn. Clone Git không tự tạo đường truy cập từ điện thoại và không tự kết nối một plugin ChatGPT.

## Agent chỉnh trực tiếp

Sau read, lấy `revision`. Tạo file arguments.json (ví dụ dưới đây dùng revision 0 cho workspace mới):

```json
{
  "baseRevision": 0,
  "requestId": "agent-root-key-0001",
  "operations": [{"type":"bone-key","clip":"idle_se","bone":"root","time":250,"values":{"rotation":12}}]
}
```

```sh
npm run studio -- call studio_edit --args-file arguments.json
```

Editor kiểm tra thay đổi mỗi khoảng 2 giây và tải source mới khi không có bản đang chỉnh chưa đồng bộ. Nếu đang kéo hoặc có draft/xung đột, editor giữ bản đó và yêu cầu chọn cách giải quyết. Dùng requestId mới cho lệnh mới; khi thử lại vì mất phản hồi, giữ nguyên requestId và toàn bộ arguments. Lỗi 409 cần read và xem thay đổi trước khi quyết định áp dụng lại.

Các tool: studio_open/read/edit/view/undo/redo/replace/check/poll. Edit hỗ trợ batch 1–50 operations, IK, bone/slot keys, clips, retime, events, sockets, trang bị và các operations của rig-core. View chỉ chọn clip/xương/thời gian/tool, không thêm undo. Undo/redo dùng baseRevision và requestId như edit. Xem docs/AGENT.md và cli/references/agent-workflow.md để biết operations; gọi studio_check để kiểm tra nguồn. Source chung tối đa 4 MB, history tối đa 20 bước/khoảng 8 MB.

Prompt cho agent:

> Đọc AGENTS.md, khởi chạy editor nếu môi trường hỗ trợ mở port. Dùng studio read và CLI/MCP để chỉnh project chung theo yêu cầu của tôi. Sau mỗi batch báo revision, thao tác đã thực hiện và kết quả check. Giữ draft khi xung đột. Xuất source JSON trước khi bàn giao.

## MCP local

`config/mcp.example.json` là mẫu cho host có cấu hình mcpServers. Thay cả hai đường dẫn tuyệt đối. Host khác có thể dùng định dạng cấu hình khác. Lệnh server là `node /ABSOLUTE/REPO/local/mcp-stdio.mjs --data /ABSOLUTE/REPO/.studio`.

Editor, CLI và MCP phải trỏ vào **cùng đường dẫn --data**. Mặc định dữ liệu nằm trong .studio ngay tại repository, không phụ thuộc cwd. Ví dụ workspace riêng:

```sh
npm start -- --data /absolute/path/my-workspace
npm run studio -- read --data /absolute/path/my-workspace
```

MCP stdio chỉ ghi JSON-RPC lên stdout; stderr dùng báo lỗi. Cấu hình xong cần host thực sự khởi chạy và kết nối server. Khi host chưa hỗ trợ local MCP, agent có terminal vẫn thao tác được bằng CLI. Không có API key/model agent kèm trong ZIP.

## Lưu và đưa lên Git

Server lưu .studio/state.json bằng thay file nguyên tử và kiểm tra revision dưới khóa liên tiến trình. Restart giữ project, undo/redo và trạng thái chọn; cookie phiên local đổi khi server khởi động lại. Dữ liệu trình duyệt/snapshot là lớp phục hồi riêng. .studio bị loại khỏi Git và ZIP; dữ liệu bạn chỉnh không tự trở thành commit.

```sh
npm run studio -- export projects/hero.rig.json
npm run studio -- read
npm run studio -- import projects/hero.rig.json --revision 7
```

Thay 7 bằng revision vừa đọc. Export từ chối ghi đè, chọn tên mới. Import validate trước khi ghi; không sửa state.json trực tiếp. Để push Git: giải nén, git init nếu chưa có repository, git add/commit source rồi thêm remote của bạn và push. Giữ .gitignore; kiểm tra source JSON và ảnh trước khi đưa repository công khai. ZIP không có project cá nhân, credential, node_modules hoặc dữ liệu phiên local.

Mở Nhon-Le-Sprite-Studio.html vẫn dùng được offline riêng; bản này không chia sẻ .studio. Muốn agent và người cùng thấy chỉnh sửa, dùng editor qua npm start. Dùng CLI rig-tool trên JSON riêng cũng cần import lại để cập nhật project chung.

## Phục hồi và kiểm tra

```sh
npm run studio -- doctor
npm run studio -- unlock
npm test
```

Doctor chỉ báo đường dẫn/khóa; unlock chỉ xóa khóa khi PID chủ sở hữu đã dừng. Nếu khóa hỏng hoặc PID đã được tái sử dụng, dừng toàn bộ tiến trình editor/MCP/CLI rồi kiểm tra write.lock thủ công. State hỏng được báo lỗi và giữ nguyên, không tự reset; phục hồi từ JSON/backup đã xuất. Không có bảo đảm mất điện, ổ đĩa lỗi hay khóa file trên network filesystem; dùng ổ đĩa local và xuất nguồn định kỳ.

npm test không cần canvas: test editor API trong bộ xử lý Fetch, CLI/MCP chạy tiến trình thật, CAS liên tiến trình, auth/origin, restart và các test service/bridge/vault. Đã kiểm tra HTTP listener qua client HTTP thật với npm run test:field; chưa kiểm tra browser thật, CSS/touch, host MCP cụ thể hoặc engine game; xem docs/QA.md. Node/Python/canvas không được nhúng vào ZIP.

Toàn bộ skill v3.8 đã tích hợp ở skills/produce-game-sprites. Đọc docs/INTEGRATION.md và áp dụng qua AGENTS.md; dùng npm run art cho production QA.

Chế độ Sites là lựa chọn khác; .openai/hosting.json đang tham chiếu Site gốc. Không tự publish manifest này khi clone sang tài khoản khác; thiết lập project/hosting riêng nếu cần. Bản local không cần dùng manifest đó.

Field test: npm run test:field chạy server tạm trên loopback và tự đóng khi kết thúc. Bao gồm nối lại cookie sau restart, lỗi mạng/lost reply, CAS sáu tiến trình, giới hạn byte UTF-8 và SIGKILL trước atomic rename. Sau restart, tab local tự xin cookie mới rồi thử lại cùng arguments; không cần đăng nhập ChatGPT. Các ca này dùng mô hình DOM tối giản cho bridge, không kiểm chứng CSS/touch. Đọc docs/FIELD-TEST.md.

VFX/asset operations and effect selection share this same state. Read [PRODUCTION.md](PRODUCTION.md); use npm run production for separate VFX render/source bundles.
