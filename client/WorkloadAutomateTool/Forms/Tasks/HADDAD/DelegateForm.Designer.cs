namespace WorkloadAutomateTool.Forms.Tasks.HADDAD
{
    public partial class DelegateForm
    {
        private System.ComponentModel.IContainer components = null;

        private System.Windows.Forms.Button btnOpenPhoto8;
        private System.Windows.Forms.Button btnOpenPdfToExcel;
        private System.Windows.Forms.Button btnOpenCostingSheet;
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

            this.btnOpenPhoto8 = new System.Windows.Forms.Button();
            this.btnOpenPdfToExcel = new System.Windows.Forms.Button();
            this.btnOpenCostingSheet = new System.Windows.Forms.Button();
            this.btnBack = new System.Windows.Forms.Button();

            this.SuspendLayout();

            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(500, 350);
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Delegate Function";
            this.Font = new System.Drawing.Font("Segoe UI", 12F);

            this.btnOpenPhoto8.Location = new System.Drawing.Point(50, 50);
            this.btnOpenPhoto8.Size = new System.Drawing.Size(400, 60);
            this.btnOpenPhoto8.Text = "Photo 8 Upload";
            this.btnOpenPhoto8.UseVisualStyleBackColor = true;
            this.btnOpenPhoto8.Click += new System.EventHandler(this.btnOpenPhoto8_Click);

            this.btnOpenPdfToExcel.Location = new System.Drawing.Point(50, 130);
            this.btnOpenPdfToExcel.Size = new System.Drawing.Size(400, 60);
            this.btnOpenPdfToExcel.Text = "PDF to Excel";
            this.btnOpenPdfToExcel.UseVisualStyleBackColor = true;
            this.btnOpenPdfToExcel.Click += new System.EventHandler(this.btnOpenPdfToExcel_Click);

            this.btnOpenCostingSheet.Location = new System.Drawing.Point(50, 210);
            this.btnOpenCostingSheet.Size = new System.Drawing.Size(400, 60);
            this.btnOpenCostingSheet.Text = "Costing Sheet";
            this.btnOpenCostingSheet.UseVisualStyleBackColor = true;
            this.btnOpenCostingSheet.Click += new System.EventHandler(this.btnOpenCostingSheet_Click);

            this.btnBack.Location = new System.Drawing.Point(50, 290);
            this.btnBack.Size = new System.Drawing.Size(400, 40);
            this.btnBack.Text = "Back";
            this.btnBack.UseVisualStyleBackColor = true;
            this.btnBack.Click += new System.EventHandler(this.btnBack_Click);

            this.Controls.Add(this.btnOpenPhoto8);
            this.Controls.Add(this.btnOpenPdfToExcel);
            this.Controls.Add(this.btnOpenCostingSheet);
            this.Controls.Add(this.btnBack);

            this.ResumeLayout(false);
        }
    }
}
