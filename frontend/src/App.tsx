import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RoleGuard } from "./auth/RoleGuard";
import { DashboardLayout } from "./components/layout/DashboardLayout";
import { adminNavItems } from "./dashboards/adminNav";
import { doctorNavItems } from "./dashboards/doctorNav";
import { labStaffNavItems } from "./dashboards/labStaffNav";
import { patientNavItems } from "./dashboards/patientNav";
import { receptionistNavItems } from "./dashboards/receptionistNav";
import { DashboardPendingPage } from "./pages/DashboardPendingPage";
import { AdminAnalyticsPage } from "./pages/admin/AdminAnalyticsPage";
import { AdminAuditLogsPage } from "./pages/admin/AdminAuditLogsPage";
import { AdminBillingPage } from "./pages/admin/AdminBillingPage";
import { AdminDepartmentsPage } from "./pages/admin/AdminDepartmentsPage";
import { AdminDoctorsPage } from "./pages/admin/AdminDoctorsPage";
import { AdminOverviewPage } from "./pages/admin/AdminOverviewPage";
import { AdminSettingsPage } from "./pages/admin/AdminSettingsPage";
import { AdminUsersPage } from "./pages/admin/AdminUsersPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { DoctorActivityPage } from "./pages/doctor/DoctorActivityPage";
import { DoctorAppointmentsPage } from "./pages/doctor/DoctorAppointmentsPage";
import { DoctorAvailabilityPage } from "./pages/doctor/DoctorAvailabilityPage";
import { DoctorLabRequestsPage } from "./pages/doctor/DoctorLabRequestsPage";
import { DoctorPrescriptionsPage } from "./pages/doctor/DoctorPrescriptionsPage";
import { DoctorQueuePage } from "./pages/doctor/DoctorQueuePage";
import { DoctorRecordsPage } from "./pages/doctor/DoctorRecordsPage";
import { LabPendingTestsPage } from "./pages/labstaff/LabPendingTestsPage";
import { LabProcessingPage } from "./pages/labstaff/LabProcessingPage";
import { LabReportsListPage } from "./pages/labstaff/LabReportsListPage";
import { AppointmentsPage } from "./pages/patient/AppointmentsPage";
import { BillingPage } from "./pages/patient/BillingPage";
import { LabReportsPage } from "./pages/patient/LabReportsPage";
import { MedicalRecordsPage } from "./pages/patient/MedicalRecordsPage";
import { PatientHome } from "./pages/patient/PatientHome";
import { PrescriptionsPage } from "./pages/patient/PrescriptionsPage";
import { TriagePage } from "./pages/patient/TriagePage";
import { ReceptionistQueuePage } from "./pages/receptionist/ReceptionistQueuePage";
import { WalkInRegistrationPage } from "./pages/receptionist/WalkInRegistrationPage";
import { MessagesPage } from "./pages/shared/MessagesPage";
import { NotificationsPage } from "./pages/shared/NotificationsPage";
import { PatientsSearchPage } from "./pages/shared/PatientsSearchPage";
import { StaffAppointmentsPage } from "./pages/shared/StaffAppointmentsPage";
import { landingPathForRole } from "./roleRouting";

function RootRedirect() {
  const { user, isLoading } = useAuth();
  if (isLoading) return null;
  return <Navigate to={user ? landingPathForRole(user.role) : "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard-pending" element={<DashboardPendingPage />} />

        {/* --- Patient --- */}
        <Route
          path="/patient"
          element={
            <RoleGuard role="patient">
              <DashboardLayout items={patientNavItems} roleLabel="Patient" title="Patient Portal" notificationsPath="/patient/notifications" />
            </RoleGuard>
          }
        >
          <Route index element={<PatientHome />} />
          <Route path="appointments" element={<AppointmentsPage />} />
          <Route path="triage" element={<TriagePage />} />
          <Route path="records" element={<MedicalRecordsPage />} />
          <Route path="prescriptions" element={<PrescriptionsPage />} />
          <Route path="lab-reports" element={<LabReportsPage />} />
          <Route path="billing" element={<BillingPage />} />
          <Route path="messages" element={<MessagesPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        {/* --- Doctor --- */}
        <Route
          path="/doctor"
          element={
            <RoleGuard role="doctor">
              <DashboardLayout items={doctorNavItems} roleLabel="Doctor" title="Doctor Portal" notificationsPath="/doctor/notifications" />
            </RoleGuard>
          }
        >
          <Route index element={<DoctorQueuePage />} />
          <Route path="appointments" element={<DoctorAppointmentsPage />} />
          <Route path="patients" element={<PatientsSearchPage />} />
          <Route path="records" element={<DoctorRecordsPage />} />
          <Route path="prescriptions" element={<DoctorPrescriptionsPage />} />
          <Route path="lab-requests" element={<DoctorLabRequestsPage />} />
          <Route path="availability" element={<DoctorAvailabilityPage />} />
          <Route path="messages" element={<MessagesPage />} />
          <Route path="activity" element={<DoctorActivityPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        {/* --- Receptionist --- */}
        <Route
          path="/receptionist"
          element={
            <RoleGuard role="receptionist">
              <DashboardLayout
                items={receptionistNavItems}
                roleLabel="Receptionist"
                title="Front Desk"
                notificationsPath="/receptionist/notifications"
              />
            </RoleGuard>
          }
        >
          <Route index element={<ReceptionistQueuePage />} />
          <Route path="register" element={<WalkInRegistrationPage />} />
          <Route path="patients" element={<PatientsSearchPage />} />
          <Route path="appointments" element={<StaffAppointmentsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        {/* --- Lab Staff --- */}
        <Route
          path="/lab-staff"
          element={
            <RoleGuard role="lab_staff">
              <DashboardLayout items={labStaffNavItems} roleLabel="Lab Staff" title="Laboratory" notificationsPath="/lab-staff/notifications" />
            </RoleGuard>
          }
        >
          <Route index element={<LabPendingTestsPage />} />
          <Route path="processing" element={<LabProcessingPage />} />
          <Route path="reports" element={<LabReportsListPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>

        {/* --- Admin --- */}
        <Route
          path="/admin"
          element={
            <RoleGuard role="admin">
              <DashboardLayout items={adminNavItems} roleLabel="Admin" title="Administration" notificationsPath="/admin/notifications" />
            </RoleGuard>
          }
        >
          <Route index element={<AdminOverviewPage />} />
          <Route path="users" element={<AdminUsersPage />} />
          <Route path="doctors" element={<AdminDoctorsPage />} />
          <Route path="patients" element={<PatientsSearchPage />} />
          <Route path="departments" element={<AdminDepartmentsPage />} />
          <Route path="appointments" element={<StaffAppointmentsPage />} />
          <Route path="billing" element={<AdminBillingPage />} />
          <Route path="analytics" element={<AdminAnalyticsPage />} />
          <Route path="audit-logs" element={<AdminAuditLogsPage />} />
          <Route path="settings" element={<AdminSettingsPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<RootRedirect />} />
    </Routes>
  );
}
