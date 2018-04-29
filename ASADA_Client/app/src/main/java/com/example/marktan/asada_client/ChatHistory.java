package com.example.marktan.asada_client;

import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.design.widget.FloatingActionButton;
import android.support.design.widget.Snackbar;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.support.v7.widget.Toolbar;
import android.util.Log;
import android.view.View;
import android.widget.Toast;

import com.amazonaws.AmazonClientException;
import com.amazonaws.mobileconnectors.lambdainvoker.*;
import com.amazonaws.auth.CognitoCachingCredentialsProvider;
import com.amazonaws.regions.Regions;

class RequestClass {
    String type;

    public String getType(){
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public RequestClass(String type) {
        this.type = type;
    }

    public RequestClass() {}
}

class ResponseClass {
    String cookie;

    public String getCookie() {
        return this.cookie;
    }

    public void setCookie(String cookie) {
        this.cookie = cookie;
    }

    public ResponseClass(String cookie) {
        this.cookie = cookie;
    }

    public ResponseClass() {}
}

interface MyInterface {
    @LambdaFunction
        ResponseClass ASADA(RequestClass request);
}

public class ChatHistory extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_chat_history);
        Toolbar toolbar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);

        //mMessageRecycler = (RecyclerView) findViewById(R.id.reyclerview_message_list);
        //mMessageAdapter = new MessageListAdapter(this, messageList);
        //mMessageRecycler.setLayoutManager(new LinearLayoutManager(this));
        CognitoCachingCredentialsProvider cognitoProvider = new CognitoCachingCredentialsProvider(
                getApplicationContext(),
                "us-east-1:7f35985f-7d00-4360-a233-619f9c547a8f", // Identity pool ID
                Regions.US_EAST_1 // Region
        );

        LambdaInvokerFactory factory = new LambdaInvokerFactory(
                this.getApplicationContext(),
                Regions.US_EAST_1,
                cognitoProvider
        );

        final MyInterface myInterface = factory.build(MyInterface.class);

        RequestClass request = new RequestClass("FortuneCookie");

        new AsyncTask<RequestClass, Void, ResponseClass>() {
            @Override
            protected ResponseClass doInBackground(RequestClass... params) {
                // invoke "echo" method. In case it fails, it will throw a
                // LambdaFunctionException.
                try {
                    return myInterface.ASADA(params[0]);
                } catch (LambdaFunctionException lfe) {
                    Log.e("Tag", "Failed to invoke echo", lfe);
                    return null;
                } catch (AmazonClientException e) {
                    Log.e("Weird...", "Wat: " + e);
                    return null;
                }
            }

            @Override
            protected void onPostExecute(ResponseClass result) {
                if (result == null) {
                    return;
                }

                // Do a toast
                Toast.makeText(ChatHistory.this, result.getCookie(), Toast.LENGTH_LONG).show();
            }
        }.execute(request);


    }

}
