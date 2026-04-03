using System.Windows.Forms;
namespace WorkloadAutomateTool.Forms
{
    partial class MainMenu
    {
        private System.ComponentModel.IContainer components = null;
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code
        private void InitializeComponent()
        {
            this.panelHeader = new System.Windows.Forms.Panel();
            this.lblTitle = new System.Windows.Forms.Label();
            this.lblSubtitle = new System.Windows.Forms.Label();
            this.flowLayoutPanel = new System.Windows.Forms.FlowLayoutPanel();
            this.btnHaddad = new System.Windows.Forms.Button();
            this.btnLtd = new System.Windows.Forms.Button();
            this.btnGaran = new System.Windows.Forms.Button();
            this.btnExit = new System.Windows.Forms.Button();
            this.panelHeader.SuspendLayout();
            this.flowLayoutPanel.SuspendLayout();
            this.SuspendLayout();
            // 
            // panelHeader
            // 
            this.panelHeader.BackColor = System.Drawing.Color.FromArgb(0, 120, 215);
            this.panelHeader.Controls.Add(this.lblTitle);
            this.panelHeader.Controls.Add(this.lblSubtitle);
            this.panelHeader.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelHeader.Location = new System.Drawing.Point(0, 0);
            this.panelHeader.Name = "panelHeader";
            this.panelHeader.Size = new System.Drawing.Size(600, 100);
            this.panelHeader.TabIndex = 0;
            // 
            // lblTitle
            // 
            this.lblTitle.AutoSize = true;
            this.lblTitle.Font = new System.Drawing.Font("Segoe UI", 20F, System.Drawing.FontStyle.Bold);
            this.lblTitle.ForeColor = System.Drawing.Color.White;
            this.lblTitle.Location = new System.Drawing.Point(150, 20);
            this.lblTitle.Name = "lblTitle";
            this.lblTitle.Size = new System.Drawing.Size(300, 37);
            this.lblTitle.TabIndex = 0;
            this.lblTitle.Text = "Workload Automate Tool";
            // 
            // lblSubtitle
            // 
            this.lblSubtitle.AutoSize = true;
            this.lblSubtitle.Font = new System.Drawing.Font("Segoe UI", 12F);
            this.lblSubtitle.ForeColor = System.Drawing.Color.White;
            this.lblSubtitle.Location = new System.Drawing.Point(225, 60);
            this.lblSubtitle.Name = "lblSubtitle";
            this.lblSubtitle.Size = new System.Drawing.Size(150, 21);
            this.lblSubtitle.TabIndex = 1;
            this.lblSubtitle.Text = "Select Customer";
            // 
            // flowLayoutPanel
            // 
            this.flowLayoutPanel.Controls.Add(this.btnHaddad);
            this.flowLayoutPanel.Controls.Add(this.btnLtd);
            this.flowLayoutPanel.Controls.Add(this.btnGaran);
            this.flowLayoutPanel.Controls.Add(this.btnExit);
            this.flowLayoutPanel.Dock = System.Windows.Forms.DockStyle.Fill;
            this.flowLayoutPanel.FlowDirection = System.Windows.Forms.FlowDirection.TopDown;
            this.flowLayoutPanel.Location = new System.Drawing.Point(0, 100);
            this.flowLayoutPanel.Name = "flowLayoutPanel";
            this.flowLayoutPanel.Padding = new System.Windows.Forms.Padding(20);
            this.flowLayoutPanel.Size = new System.Drawing.Size(600, 300);
            this.flowLayoutPanel.TabIndex = 1;
            this.flowLayoutPanel.WrapContents = false;
            // 
            // btnHaddad
            // 
            this.btnHaddad.BackColor = System.Drawing.Color.FromArgb(0, 120, 215);
            this.btnHaddad.FlatAppearance.BorderSize = 0;
            this.btnHaddad.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold);
            this.btnHaddad.ForeColor = System.Drawing.Color.White;
            this.btnHaddad.Location = new System.Drawing.Point(23, 23);
            this.btnHaddad.Name = "btnHaddad";
            this.btnHaddad.Size = new System.Drawing.Size(250, 60);
            this.btnHaddad.TabIndex = 0;
            this.btnHaddad.Text = "HADDAD";
            this.btnHaddad.UseVisualStyleBackColor = false;
            this.btnHaddad.Click += new System.EventHandler(this.BtnHaddad_Click);
            // 
            // btnLtd
            // 
            this.btnLtd.BackColor = System.Drawing.Color.FromArgb(0, 150, 0);
            this.btnLtd.FlatAppearance.BorderSize = 0;
            this.btnLtd.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold);
            this.btnLtd.ForeColor = System.Drawing.Color.White;
            this.btnLtd.Location = new System.Drawing.Point(23, 89);
            this.btnLtd.Name = "btnLtd";
            this.btnLtd.Size = new System.Drawing.Size(250, 60);
            this.btnLtd.TabIndex = 1;
            this.btnLtd.Text = "LTD";
            this.btnLtd.UseVisualStyleBackColor = false;
            this.btnLtd.Click += new System.EventHandler(this.BtnLtd_Click);
            // 
            // btnGaran
            // 
            this.btnGaran.BackColor = System.Drawing.Color.FromArgb(255, 140, 0);
            this.btnGaran.FlatAppearance.BorderSize = 0;
            this.btnGaran.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold);
            this.btnGaran.ForeColor = System.Drawing.Color.White;
            this.btnGaran.Location = new System.Drawing.Point(23, 155);
            this.btnGaran.Name = "btnGaran";
            this.btnGaran.Size = new System.Drawing.Size(250, 60);
            this.btnGaran.TabIndex = 2;
            this.btnGaran.Text = "GARAN";
            this.btnGaran.UseVisualStyleBackColor = false;
            this.btnGaran.Click += new System.EventHandler(this.BtnGaran_Click);
            // 
            // btnExit
            // 
            this.btnExit.BackColor = System.Drawing.Color.FromArgb(128, 128, 128);
            this.btnExit.FlatAppearance.BorderSize = 0;
            this.btnExit.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold);
            this.btnExit.ForeColor = System.Drawing.Color.White;
            this.btnExit.Location = new System.Drawing.Point(23, 221);
            this.btnExit.Name = "btnExit";
            this.btnExit.Size = new System.Drawing.Size(250, 60);
            this.btnExit.TabIndex = 3;
            this.btnExit.Text = "EXIT";
            this.btnExit.UseVisualStyleBackColor = false;
            this.btnExit.Click += new System.EventHandler(this.BtnExit_Click);
            // 
            // MainMenu
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(600, 400);
            this.Controls.Add(this.flowLayoutPanel);
            this.Controls.Add(this.panelHeader);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Name = "MainMenu";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Workload Automate Tool";
            this.Load += new System.EventHandler(this.MainMenu_Load);
            this.panelHeader.ResumeLayout(false);
            this.panelHeader.PerformLayout();
            this.flowLayoutPanel.ResumeLayout(false);
            this.ResumeLayout(false);
        }
        #endregion
        private System.Windows.Forms.Panel panelHeader;
        private System.Windows.Forms.Label lblTitle;
        private System.Windows.Forms.Label lblSubtitle;
        private System.Windows.Forms.FlowLayoutPanel flowLayoutPanel;
        private System.Windows.Forms.Button btnHaddad;
        private System.Windows.Forms.Button btnLtd;
        private System.Windows.Forms.Button btnGaran;
        private System.Windows.Forms.Button btnExit;
    }
}