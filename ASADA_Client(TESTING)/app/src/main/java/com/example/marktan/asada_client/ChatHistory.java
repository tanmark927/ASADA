package com.example.marktan.asada_client;

import android.content.Intent;
import android.content.pm.PackageInstaller;
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

import java.lang.annotation.RetentionPolicy;

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

//THIS IS POTENTIAL ASADA CODE
class OutputSpeech{
    public String getSpeechtype() {
        return speechtype;
    }

    public void setSpeechtype(String speechtype) {
        this.speechtype = speechtype;
    }

    String speechtype;

    public String getSpeechtext() {
        return speechtext;
    }

    public void setSpeechtext(String speechtext) {
        this.speechtext = speechtext;
    }

    String speechtext;

    public OutputSpeech() {}
    public OutputSpeech(String type, String text)
    {
        this.speechtype = type;
        this.speechtext = text;
    }
}

class Card{
    public String getSpeechtype() {
        return speechtype;
    }

    public void setSpeechtype(String speechtype) {
        this.speechtype = speechtype;
    }

    String speechtype;

    public String getSpeechtitle() {
        return speechtitle;
    }

    public void setSpeechtitle(String speechtitle) {
        this.speechtitle = speechtitle;
    }

    String speechtitle;

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    String content;

    public Card() {}
    public Card(String sType, String sTitle, String c)
    {
        this.speechtype = sType;
        this.speechtitle = sTitle;
        this.content = c;
    }
}

class Reprompt{
    public OutputSpeech getOs() {
        return os;
    }

    public void setOs(OutputSpeech os) {
        this.os = os;
    }

    OutputSpeech os;

    public Reprompt() {}
    public Reprompt(OutputSpeech os){
        this.os = os;
    }

}

class SessionAttribute{
    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    String key;

    public String getVal() {
        return val;
    }

    public void setVal(String val) {
        this.val = val;
    }

    String val;

    public SessionAttribute() {}
    public SessionAttribute(String k, String v)
    {
        this.key = k;
        this.val = v;
    }

}

class Speechlet{
    OutputSpeech os;
    Card c;
    Reprompt re;
    boolean shouldEndSession;

    public Speechlet() {}
    public Speechlet(OutputSpeech os, Card c, Reprompt re, boolean ses)
    {
        this.os = os;
        this.c = c;
        this.re = re;
        this.shouldEndSession = ses;
    }
    public OutputSpeech getOutput() {
        return this.os;
    }

    public void setOutput(OutputSpeech s) { this.os = s; }

    public Card getCard() {
        return this.c;
    }

    public void setCard(Card c) {
        this.c = c;
    }

    public Reprompt getReprompt() {
        return this.re;
    }

    public void setReprompt(Reprompt r) { this.re = r; }

    public boolean getSES() {
        return this.shouldEndSession;
    }

    public void setSES(boolean ses) {
        this.shouldEndSession = ses;
    }
}

class Response2{
    String version;
    SessionAttribute sa;
    Speechlet resp;

    public Response2() {}
    public Response2(String v, SessionAttribute sa, Speechlet r)
    {
        this.version = v;
        this.sa = sa;
        this.resp = r;
    }

    public String getVer() {
        return this.version;
    }

    public void setVer(String v) {
        this.version = v;
    }

    public SessionAttribute getSessAtt() {
        return this.sa;
    }

    public void setSessAtt(SessionAttribute s) { this.sa = s; }

    public Speechlet getResp() {
        return this.resp;
    }

    public void setCookie(Speechlet r) {
        this.resp = r;
    }
}

////

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
                "us-east-1:e3c204de-26f2-4616-b3a3-2d0a429f4d14", // Identity pool ID
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
                // TODO
                // save user input into client
                // so CLIENT MUST listen to user input live
                // print each into a chat bubble

                // Do a toast
                Toast.makeText(ChatHistory.this, result.getCookie(), Toast.LENGTH_LONG).show();
            }
        }.execute(request);


    }

}
