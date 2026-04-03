namespace WorkloadAutomateTool.Forms.Tasks.HADDAD
{
    public partial class CostingForm
    {
        private System.ComponentModel.IContainer components = null;

        private System.Windows.Forms.Panel cs_pnlTop;
        private System.Windows.Forms.Label cs_lblServer;
        private System.Windows.Forms.TextBox cs_txtServerUrl;
        private System.Windows.Forms.Label cs_lblUser;
        private System.Windows.Forms.TextBox cs_txtUsername;
        private System.Windows.Forms.Label cs_lblPass;
        private System.Windows.Forms.TextBox cs_txtPassword;
        private System.Windows.Forms.Button cs_btnLogin;

        private System.Windows.Forms.Label cs_lblBrand;
        private System.Windows.Forms.ComboBox cs_cboBrand;
        private System.Windows.Forms.Button cs_btnLoadData;
        private System.Windows.Forms.Button cs_btnExportExcel;
        private System.Windows.Forms.Label cs_lblStatus;

        private System.Windows.Forms.DataGridView cs_dgvData;

        private System.Windows.Forms.GroupBox cs_grpLog;
        private System.Windows.Forms.TextBox cs_txtLog;

        private System.Windows.Forms.Button cs_btnClearLog;
        private System.Windows.Forms.Button cs_btnCopyLog;

        private System.Windows.Forms.Button btnBack;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
                components.Dispose();
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();

            this.cs_pnlTop = new System.Windows.Forms.Panel();
            this.cs_lblServer = new System.Windows.Forms.Label();
            this.cs_txtServerUrl = new System.Windows.Forms.TextBox();
            this.cs_lblUser = new System.Windows.Forms.Label();
            this.cs_txtUsername = new System.Windows.Forms.TextBox();
            this.cs_lblPass = new System.Windows.Forms.Label();
            this.cs_txtPassword = new System.Windows.Forms.TextBox();
            this.cs_btnLogin = new System.Windows.Forms.Button();

            this.cs_lblBrand = new System.Windows.Forms.Label();
            this.cs_cboBrand = new System.Windows.Forms.ComboBox();
            this.cs_btnLoadData = new System.Windows.Forms.Button();
            this.cs_btnExportExcel = new System.Windows.Forms.Button();
            this.cs_lblStatus = new System.Windows.Forms.Label();

            this.cs_dgvData = new System.Windows.Forms.DataGridView();

            this.cs_grpLog = new System.Windows.Forms.GroupBox();
            this.cs_txtLog = new System.Windows.Forms.TextBox();
            this.cs_btnClearLog = new System.Windows.Forms.Button();
            this.cs_btnCopyLog = new System.Windows.Forms.Button();

            this.btnBack = new System.Windows.Forms.Button();

            this.cs_pnlTop.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.cs_dgvData)).BeginInit();
            this.cs_grpLog.SuspendLayout();
            this.SuspendLayout();

            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1200, 700);
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Costing Sheet";
            this.Font = new System.Drawing.Font("Segoe UI", 9F);

            this.cs_pnlTop.Dock = System.Windows.Forms.DockStyle.Top;
            this.cs_pnlTop.Height = 120;
            this.cs_pnlTop.Padding = new System.Windows.Forms.Padding(12);

            this.cs_lblServer.AutoSize = true;
            this.cs_lblServer.Location = new System.Drawing.Point(12, 10);
            this.cs_lblServer.Text = "Server URL";

            this.cs_txtServerUrl.Location = new System.Drawing.Point(12, 30);
            this.cs_txtServerUrl.Size = new System.Drawing.Size(360, 23);
            this.cs_txtServerUrl.Text = "http://127.0.0.1:8000";

            this.cs_lblUser.AutoSize = true;
            this.cs_lblUser.Location = new System.Drawing.Point(390, 10);
            this.cs_lblUser.Text = "Username";

            this.cs_txtUsername.Location = new System.Drawing.Point(390, 30);
            this.cs_txtUsername.Size = new System.Drawing.Size(150, 23);

            this.cs_lblPass.AutoSize = true;
            this.cs_lblPass.Location = new System.Drawing.Point(555, 10);
            this.cs_lblPass.Text = "Password";

            this.cs_txtPassword.Location = new System.Drawing.Point(555, 30);
            this.cs_txtPassword.Size = new System.Drawing.Size(150, 23);
            this.cs_txtPassword.UseSystemPasswordChar = true;

            this.cs_btnLogin.Location = new System.Drawing.Point(720, 27);
            this.cs_btnLogin.Size = new System.Drawing.Size(90, 28);
            this.cs_btnLogin.Text = "Login";
            this.cs_btnLogin.UseVisualStyleBackColor = true;
            this.cs_btnLogin.Click += new System.EventHandler(this.cs_btnLogin_Click);

            this.cs_lblBrand.AutoSize = true;
            this.cs_lblBrand.Location = new System.Drawing.Point(12, 64);
            this.cs_lblBrand.Text = "Brand";

            this.cs_cboBrand.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cs_cboBrand.FormattingEnabled = true;
            this.cs_cboBrand.Items.AddRange(new object[] { "HADDAD" });
            this.cs_cboBrand.Location = new System.Drawing.Point(12, 86);
            this.cs_cboBrand.Size = new System.Drawing.Size(150, 24);
            this.cs_cboBrand.SelectedIndex = 0;

            this.cs_btnLoadData.Location = new System.Drawing.Point(180, 84);
            this.cs_btnLoadData.Size = new System.Drawing.Size(120, 26);
            this.cs_btnLoadData.Text = "Load Data";
            this.cs_btnLoadData.UseVisualStyleBackColor = true;
            this.cs_btnLoadData.Click += new System.EventHandler(this.cs_btnLoadData_Click);

            this.cs_btnExportExcel.Location = new System.Drawing.Point(310, 84);
            this.cs_btnExportExcel.Size = new System.Drawing.Size(120, 26);
            this.cs_btnExportExcel.Text = "Export Excel";
            this.cs_btnExportExcel.UseVisualStyleBackColor = true;
            this.cs_btnExportExcel.Click += new System.EventHandler(this.cs_btnExportExcel_Click);

            this.cs_lblStatus.Location = new System.Drawing.Point(450, 84);
            this.cs_lblStatus.Size = new System.Drawing.Size(400, 26);
            this.cs_lblStatus.Text = "Status: Not logged in";
            this.cs_lblStatus.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;

            this.cs_btnClearLog.Location = new System.Drawing.Point(870, 84);
            this.cs_btnClearLog.Size = new System.Drawing.Size(80, 26);
            this.cs_btnClearLog.Text = "Clear Log";
            this.cs_btnClearLog.UseVisualStyleBackColor = true;
            this.cs_btnClearLog.Click += new System.EventHandler(this.cs_btnClearLog_Click);

            this.cs_btnCopyLog.Location = new System.Drawing.Point(960, 84);
            this.cs_btnCopyLog.Size = new System.Drawing.Size(80, 26);
            this.cs_btnCopyLog.Text = "Copy Log";
            this.cs_btnCopyLog.UseVisualStyleBackColor = true;
            this.cs_btnCopyLog.Click += new System.EventHandler(this.cs_btnCopyLog_Click);

            this.btnBack.Location = new System.Drawing.Point(1050, 84);
            this.btnBack.Size = new System.Drawing.Size(90, 26);
            this.btnBack.Text = "Back";
            this.btnBack.UseVisualStyleBackColor = true;
            this.btnBack.Click += new System.EventHandler(this.btnBack_Click);

            this.cs_pnlTop.Controls.Add(this.cs_lblServer);
            this.cs_pnlTop.Controls.Add(this.cs_txtServerUrl);
            this.cs_pnlTop.Controls.Add(this.cs_lblUser);
            this.cs_pnlTop.Controls.Add(this.cs_txtUsername);
            this.cs_pnlTop.Controls.Add(this.cs_lblPass);
            this.cs_pnlTop.Controls.Add(this.cs_txtPassword);
            this.cs_pnlTop.Controls.Add(this.cs_btnLogin);

            this.cs_pnlTop.Controls.Add(this.cs_lblBrand);
            this.cs_pnlTop.Controls.Add(this.cs_cboBrand);
            this.cs_pnlTop.Controls.Add(this.cs_btnLoadData);
            this.cs_pnlTop.Controls.Add(this.cs_btnExportExcel);
            this.cs_pnlTop.Controls.Add(this.cs_lblStatus);
            this.cs_pnlTop.Controls.Add(this.cs_btnClearLog);
            this.cs_pnlTop.Controls.Add(this.cs_btnCopyLog);
            this.cs_pnlTop.Controls.Add(this.btnBack);

            this.cs_dgvData.AllowUserToAddRows = false;
            this.cs_dgvData.AllowUserToDeleteRows = false;
            this.cs_dgvData.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.cs_dgvData.Dock = System.Windows.Forms.DockStyle.Top;
            this.cs_dgvData.Location = new System.Drawing.Point(0, 120);
            this.cs_dgvData.Name = "cs_dgvData";
            this.cs_dgvData.ReadOnly = true;
            this.cs_dgvData.RowTemplate.Height = 24;
            this.cs_dgvData.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
            this.cs_dgvData.Size = new System.Drawing.Size(1200, 400);

            this.cs_grpLog.Dock = System.Windows.Forms.DockStyle.Fill;
            this.cs_grpLog.Text = "Log";
            this.cs_grpLog.Padding = new System.Windows.Forms.Padding(10);

            this.cs_txtLog.Dock = System.Windows.Forms.DockStyle.Fill;
            this.cs_txtLog.Multiline = true;
            this.cs_txtLog.ScrollBars = System.Windows.Forms.ScrollBars.Both;
            this.cs_txtLog.WordWrap = false;

            this.cs_grpLog.Controls.Add(this.cs_txtLog);

            this.Controls.Add(this.cs_grpLog);
            this.Controls.Add(this.cs_dgvData);
            this.Controls.Add(this.cs_pnlTop);

            this.cs_pnlTop.ResumeLayout(false);
            this.cs_pnlTop.PerformLayout();

            ((System.ComponentModel.ISupportInitialize)(this.cs_dgvData)).EndInit();

            this.cs_grpLog.ResumeLayout(false);
            this.cs_grpLog.PerformLayout();

            this.ResumeLayout(false);
        }
    }
}
